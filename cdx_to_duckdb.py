import argparse
import duckdb
import os
import glob

def connect_db(db_file):
    """Establishes a connection to the DuckDB database."""
    return duckdb.connect(database=db_file, read_only=False)

def create_cdx_table(conn, table_name):
    """Creates the CDX table if it doesn't exist."""
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        urlkey VARCHAR,
        timestamp VARCHAR,
        url VARCHAR,
        mime VARCHAR,
        status VARCHAR,
        digest VARCHAR,
        redirect VARCHAR,
        meta VARCHAR,
        length BIGINT,
        "offset" BIGINT,
        filename VARCHAR
    );
    """

    try:
        conn.execute(create_table_sql)
        print(f"Table '{table_name}' created successfully or already exists.")
    except Exception as e:
        print(f"Error creating table {table_name}: {e}")
        raise

def truncate_table(conn, table_name):
    """Drops the specified table."""
    try:
        conn.execute(f"DROP TABLE IF EXISTS {table_name};")
        print(f"Table '{table_name}' dropped successfully.")
    except Exception as e:
        print(f"Error dropping table {table_name}: {e}")
        # We might not want to raise here if the goal is to recreate it anyway
        # but for now, let's be explicit about errors.
        raise

def ingest_cdx_file(conn, table_name, cdx_file_path):
    """Ingests a single CDX file into the specified table."""
    print(f"Ingesting {cdx_file_path} into {table_name}...")
    try:
        # Read the first line to check if it's a CDX header
        header_line = ''
        try:
            with open(cdx_file_path, 'r') as f:
                header_line = f.readline().strip()
        except Exception:
            # Ignore if file can't be read for header check, proceed as if no header
            pass

        skip_header = 0
        if header_line.startswith(" CDX") or header_line.startswith("!context"): # Common CDX headers
            skip_header = 1
            print(f"Detected header in {cdx_file_path}, skipping first line.")

        # Define columns for read_csv to match the expected CDX fields.
        # If the CDX file has fewer columns, null_padding will handle it.
        # If it has more, they will be ignored by the explicit column selection in the INSERT statement.
        # The 'offset' field is read as 'offset_str' (VARCHAR) and then cast to BIGINT.
        ingest_query = f"""
        INSERT INTO {table_name} (urlkey, timestamp, url, mime, status, digest, redirect, meta, length, "offset", filename)
        SELECT
            parsed_csv.urlkey,
            parsed_csv.timestamp,
            parsed_csv.url,
            parsed_csv.mime,
            parsed_csv.status,
            parsed_csv.digest,
            parsed_csv.redirect,
            parsed_csv.meta,
            TRY_CAST(parsed_csv.length AS BIGINT),
            TRY_CAST(parsed_csv."offset" AS BIGINT),  -- Ensure offset is BIGINT
            parsed_csv.filename
        FROM read_csv('{cdx_file_path}',
            header=false,
            delim=' ',
            skip={skip_header},
            null_padding=true,
            columns={{
                'urlkey': 'VARCHAR',
                'timestamp': 'VARCHAR',
                'url': 'VARCHAR',
                'mime': 'VARCHAR',
                'status': 'VARCHAR',
                'digest': 'VARCHAR',
                'redirect': 'VARCHAR',
                'meta': 'VARCHAR',
                'length': 'VARCHAR',
                'offset': 'VARCHAR',
                'filename': 'VARCHAR'
            }},
            auto_detect=false,
            strict_mode=false
        ) AS parsed_csv
        ORDER BY urlkey, timestamp;
        """
        conn.execute(ingest_query)
        print(f"Successfully ingested data from {cdx_file_path}.")

    except duckdb.Error as e:
        print(f"DuckDB error ingesting {cdx_file_path}: {e}")
        print(f"Failed SQL: {ingest_query}")
    except Exception as e:
        print(f"General error ingesting {cdx_file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Ingest CDX files into a DuckDB database.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-dir", help="Directory containing CDX files.")
    group.add_argument("--input-file", help="Path to a single CDX file.")
    parser.add_argument("--db-file", required=True, help="Path to the DuckDB database file.")
    parser.add_argument("--table-name", required=True, help="Name of the table to ingest data into.")
    parser.add_argument("--create-table", action="store_true", help="Create the table if it doesn't exist.")
    parser.add_argument("--truncate", action="store_true", help="Truncate (drop and recreate) the table before ingestion.")

    args = parser.parse_args()

    # Validate input
    if args.input_dir:
        if not os.path.isdir(args.input_dir):
            print(f"Error: Input directory '{args.input_dir}' not found.")
            return
    elif args.input_file:
        if not os.path.isfile(args.input_file):
            print(f"Error: Input file '{args.input_file}' not found.")
            return

    conn = None
    try:
        conn = connect_db(args.db_file)

        if args.truncate:
            truncate_table(conn, args.table_name)
            create_cdx_table(conn, args.table_name) # Recreate after truncating
        elif args.create_table:
            create_cdx_table(conn, args.table_name)
        else:
            # Check if table exists, if not, inform user or error out
            res = conn.execute(f"SELECT 1 FROM information_schema.tables WHERE table_name = '{args.table_name}'").fetchone()
            if not res:
                print(f"Error: Table '{args.table_name}' does not exist. Use --create-table or --truncate to create it.")
                return

        # Determine files to ingest
        if args.input_file:
            cdx_files = [args.input_file]
        else:
            cdx_files = glob.glob(os.path.join(args.input_dir, "*.cdx"))
            if not cdx_files:
                print(f"No .cdx files found in '{args.input_dir}'.")
                return

        for cdx_file in cdx_files:
            ingest_cdx_file(conn, args.table_name, cdx_file)

        # Sort the table by urlkey and timestamp
        conn.execute(f"CREATE OR REPLACE TABLE {args.table_name} AS SELECT * FROM {args.table_name} ORDER BY urlkey, \"timestamp\";")
        # Remove rows where urlkey is null
        conn.execute(f"DELETE FROM {args.table_name} WHERE urlkey IS NULL;")

        print("Ingestion process completed.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 