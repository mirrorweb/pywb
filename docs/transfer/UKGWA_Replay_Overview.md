# UKGWA Replay / PyWB Surface — How It Works

| Field | Value |
|---|---|
| **Audience** | The National Archives (TNA) and MirrorWeb stakeholders |
| **Companion document** | [UKGWA Replay / PyWB Surface — Technical Documentation](./UKGWA_Replay_Technical_Documentation.md) |
| **Last updated** | 2026-08-03 |

This note explains how people **view** archived UK Government Web Archive captures in a browser: the replay engine, branding/themes, site-specific fix-ups, error pages, and legacy URL redirects.

---

## 1. What replay is

**Replay** shows a specific capture of a URL at a point in time (for example `/ukgwa/{timestamp}/{url}`). It is separate from full-text search: search helps people discover captures; replay displays them.

---

## 2. Journey

```text
  User opens an archive URL (often /ukgwa/...)
              │
              ▼
     Legacy path? ──yes──► tna-qa-redirect → /ukgwa/...
              │ no
              ▼
     PyWB (mirrorweb/pywb) resolves the capture
     and rewrites the page for replay
              │
              ├── themes from tna-pywb2-themes (banner, chrome, templates)
              ├── content scripts from mw-tna-pywb-contentscripts
              │     (site-specific JS to make archived pages work)
              └── errors use tna-errorpages templates when status pages are needed
```

Access Manager rules (separate pack) may block a URL before content is shown.

---

## 3. What this pack does not cover

CI/ECS/Terraform deploy repositories for PyWB are out of scope for application code transfer. This pack describes the replay **application surface** only.
