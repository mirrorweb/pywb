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

def check_header(file_path):
    """Checks if a file has a CDX header and returns skip count."""
    skip_header = 0
    try:
        with open(file_path, 'r') as f:
            header_line = f.readline().strip()
            if header_line.startswith(" CDX") or header_line.startswith("!context"):
                skip_header = 1
                print(f"Detected header in {file_path}, skipping first line.")
    except Exception:
        # Ignore if file can't be read for header check, proceed as if no header
        pass
    return skip_header

def ingest_file(conn, table_name, file_path):
    """
    Unified function to ingest a CDX file into the DuckDB table.
    Works with both local files and S3 URIs.
    """
    print(f"Ingesting {file_path} into {table_name}...")
    
    # Determine if this is an S3 path or local file
    is_s3 = file_path.startswith("s3://")
    
    # For local files, check for a header
    skip_header = 0 if is_s3 else check_header(file_path)
    
    try:
        # Build the SQL query for ingestion with consistent parameters
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
            TRY_CAST(parsed_csv."offset" AS BIGINT),
            parsed_csv.filename
        FROM read_csv('{file_path}',
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
            strict_mode=false,
            ignore_errors=true
        ) AS parsed_csv
        ORDER BY urlkey, timestamp;
        """
        conn.execute(ingest_query)
        print(f"Successfully ingested data from {file_path}.")
        return True
    except duckdb.Error as e:
        print(f"DuckDB error ingesting {file_path}: {e}")
        return False
    except Exception as e:
        print(f"General error ingesting {file_path}: {e}")
        return False

def finalize_table(conn, table_name):
    """Final operations to clean and optimize the table after ingestion."""
    try:
        # Sort the table by urlkey and timestamp
        print("Optimizing table...")
        conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM {table_name} ORDER BY urlkey, \"timestamp\";")
        # Remove rows where urlkey is null
        conn.execute(f"""
            DELETE FROM {table_name} 
            WHERE urlkey IS NULL 
            OR timestamp IS NULL
            OR "offset" IS NULL
            OR length IS NULL
            OR filename IS NULL
        """)
        print("Table optimization completed.")
        return True
    except Exception as e:
        print(f"Error finalizing table: {e}")
        return False

def setup_database(conn, args):
    """Set up the database based on command-line arguments."""
    try:
        # Set S3 region if specified
        if args.s3_region:
            conn.execute(f"SET s3_region='{args.s3_region}';")
            print(f"S3 region set to '{args.s3_region}'")

        if args.truncate:
            truncate_table(conn, args.table_name)
            create_cdx_table(conn, args.table_name)  # Recreate after truncating
        elif args.create_table:
            create_cdx_table(conn, args.table_name)
        else:
            # Check if table exists, if not, inform user or error out
            res = conn.execute(f"SELECT 1 FROM information_schema.tables WHERE table_name = '{args.table_name}'").fetchone()
            if not res:
                print(f"Error: Table '{args.table_name}' does not exist. Use --create-table or --truncate to create it.")
                return False
        return True
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

def get_files_to_ingest(args):
    """Determine which files to ingest based on command-line arguments."""
    if args.input_file:
        if not os.path.isfile(args.input_file):
            print(f"Error: Input file '{args.input_file}' not found.")
            return []
        return [args.input_file]
    
    elif args.input_dir:
        if not os.path.isdir(args.input_dir):
            print(f"Error: Input directory '{args.input_dir}' not found.")
            return []
        cdx_files = glob.glob(os.path.join(args.input_dir, "*.cdx"))
        if not cdx_files:
            print(f"No .cdx files found in '{args.input_dir}'.")
            return []
        return cdx_files
    
    elif args.s3_file:
        return [args.s3_file]
    
    elif args.s3_prefix:
        return [args.s3_prefix]  # glob pattern for DuckDB S3
    
    return []

def main():
    """Main function that coordinates the CDX ingestion workflow."""
    parser = argparse.ArgumentParser(description="Ingest CDX files into a DuckDB database.")
    
    # Input source arguments (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-dir", help="Directory containing CDX files.")
    group.add_argument("--input-file", help="Path to a single CDX file.")
    group.add_argument("--s3-file", help="S3 URI to a single CDX file (e.g., s3://bucket/path/file.cdx)")
    group.add_argument("--s3-prefix", help="S3 URI prefix or glob for CDX files (e.g., s3://bucket/path/*.cdx)")
    
    # Database configuration arguments
    parser.add_argument("--db-file", required=True, help="Path to the DuckDB database file.")
    parser.add_argument("--table-name", required=True, help="Name of the table to ingest data into.")
    parser.add_argument("--create-table", action="store_true", help="Create the table if it doesn't exist.")
    parser.add_argument("--truncate", action="store_true", help="Truncate (drop and recreate) the table before ingestion.")
    parser.add_argument("--s3-region", help="AWS region for S3 access (e.g., us-west-2). Only needed for S3 sources.")

    args = parser.parse_args()

    # Get the list of files to ingest
    files_to_ingest = get_files_to_ingest(args)
    if not files_to_ingest:
        return

    # Connect to the database and set up the environment
    conn = None
    try:
        conn = connect_db(args.db_file)
        
        if not setup_database(conn, args):
            return

        # Ingest each file
        success_count = 0
        for file_path in files_to_ingest:
            if ingest_file(conn, args.table_name, file_path):
                success_count += 1

        # Report results
        if success_count > 0:
            if finalize_table(conn, args.table_name):
                print(f"Ingestion completed successfully. {success_count} file(s) processed.")
            else:
                print(f"Ingestion completed with errors during table finalization. {success_count} file(s) processed.")
        else:
            print("Ingestion failed. No files were successfully processed.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 