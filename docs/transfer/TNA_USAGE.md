# pywb — UKGWA / TNA usage notes

| Field | Value |
|---|---|
| **Repository** | `mirrorweb/pywb` (fork of Webrecorder pywb) |
| **TNA-oriented branch** | `tna` (also `tna-new` exists historically) |
| **Last updated** | 2026-08-03 |

## Purpose

Core Python web archiving toolkit used to **replay** UKGWA captures with high fidelity (URL rewriting, WARC/CDX resolution, banners/UI hooks).

## How TNA uses this fork

- Production UKGWA replay is based on the MirrorWeb `pywb` fork, with TNA-oriented work landing on the `tna` branch line.
- Branding and templates are supplied from `tna-pywb2-themes` (templates/static overrides).
- Site-specific fix-ups are supplied from `mw-tna-pywb-contentscripts`.
- Access checks may be integrated via takedown libraries (`pywb-takedowns` / `mw-takedowns`) depending on deployment configuration.
- Legacy inbound paths may be normalised by `tna-qa-redirect` before reaching PyWB.

## What this repository is not

This is **not** a MirrorWeb CI/infra transfer package. Upstream pywb documentation (`README.rst`, ReadTheDocs) remains the engine reference. Collection configuration, index backends, and deploy wiring are environment-specific.

## Related transfer documentation

See the Replay capability pack files alongside this note in `docs/transfer/`.
