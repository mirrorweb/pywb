# UKGWA Replay / PyWB Surface — Technical Documentation

| Field | Value |
|---|---|
| **Service** | UKGWA web archive replay (PyWB surface) |
| **Client overview** | [UKGWA Replay / PyWB Surface — How It Works](./UKGWA_Replay_Overview.md) |
| **Last updated** | 2026-08-03 |

Derived from application repositories. Deploy/CI repos are not transfer artefacts.

---

## 1. Repositories

| Repo | Role |
|---|---|
| `pywb` | MirrorWeb fork of Webrecorder pywb — core replay/rewrite toolkit used for UKGWA |
| `tna-pywb2-themes` | TNA public/QA theme templates and compiled CSS overrides for PyWB2 |
| `mw-tna-pywb-contentscripts` | Live (and legacy) per-site content scripts for replay fidelity |
| `tna-errorpages` | Shared 404/500 HTML for public front ends |
| `tna-qa-redirect` | Quart service redirecting legacy paths into `/ukgwa` |

---

## 2. Themes (`tna-pywb2-themes`)

- Base templates under `templates/`
- Per-type overrides under `type/{TYPE}/` (for example `tna`, `tnaqa`, public/QA variants with/without banner)
- Node/SCSS build via `make env` / theme build targets; symlink into a local `pywb` checkout with `make pywb-dev` or `make pywb-deploy`

---

## 3. Content scripts (`mw-tna-pywb-contentscripts`)

- `pywb2/sites/*.js` — current PyWB2 site scripts
- `pywb2/universalScript.js` — shared helpers
- `legacy/sites/*.js` — older script set retained for historical coverage

Scripts patch archived pages (DOM, network quirks, UI breakage) so government sites remain usable under replay rewriting.

---

## 4. Redirects & errors

- `tna-qa-redirect` maps `/tna/...`, `/tna_la_nhs/...`, `/nobanner/...`, and other non-`ukgwa` roots to `/ukgwa/...`
- `tna-errorpages` supplies static `404.html` / `500.html`

---

## 5. PyWB notes for transfer

Upstream documentation remains in `README.rst` / ReadTheDocs. For UKGWA, treat this fork as the replay engine that loads TNA themes and content scripts; configuration of collections and indexes is environment-specific and not documented here as infra transfer.
