# BHTDB.ai community reports

Report definitions for [BHTDB.ai](https://github.com/bhthoughts/bhtdb-ai-releases),
the read-only Oracle database assistant. Every `.json` file under [`reports/`](reports/)
is a self-contained report: a named set of read-only SQL queries plus optional
AI analysis instructions.

## Available reports

<!-- reports-table:start -->
| Report | SQLs | Author | Last updated |
|---|---|---|---|
| [Health Check](reports/health_check.json) | 87 | @bht | 2026-08-20 |
<!-- reports-table:end -->

Author and last-updated come from this repository's git history, maintained
automatically by CI — see [`index.json`](index.json).

## Using these reports

Inside BHTDB.ai, open the **Reports** tab and click **Community** — the app
lists the reports in this repository and imports the ones you choose. If a
report with the same name already exists on your machine, the app asks before
overwriting it.

The app contacts this repository **only when you click that button**, with a
plain anonymous download. Nothing about you, your machine, or your database is
ever sent.

You can also download any file from `reports/` by hand and use
**Reports → Import** in the app.

## Contributing a report

1. Build and test your report inside BHTDB.ai (Reports → New report).
2. In the report editor, click **Export** — that produces the exact JSON format
   this repository stores.
3. Open a pull request adding the file as `reports/<short-name>.json`.

Rules for contributions:

- **Read-only only.** Every SQL must be a single `SELECT`/`WITH` query. The app
  enforces this at run time (anything else is refused), but reports that try
  will not be merged.
- **Self-contained and generic.** No credentials, no host names, no schema or
  data from a real environment, and no values hardcoded from one database's
  results.
- **Named to be found.** The report `name` should say what it does; it is also
  the overwrite key on import, so make it unique and stable.
- **English preferred** for names and descriptions, so the widest audience can
  read them. The analysis instructions may pin any output language.

Report definitions in this repository are licensed under
[GPL-3.0-or-later](LICENSE), the same license as BHTDB.ai.
