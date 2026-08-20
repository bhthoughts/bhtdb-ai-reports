"""Build index.json and the README report table from git history.

Run by the repository's GitHub Action after every change under reports/ (and
runnable locally with GH_TOKEN set). Provenance comes from the commits API —
who created each report file and who last changed it, and when — so authorship
is a fact of the repository's history, never something a report file claims
about itself.
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = os.environ.get("GITHUB_REPOSITORY", "bhthoughts/bhtdb-ai-reports")
TOKEN = os.environ.get("GH_TOKEN", "")
ROOT = Path(__file__).resolve().parents[1]

TABLE_START = "<!-- reports-table:start -->"
TABLE_END = "<!-- reports-table:end -->"


def api(url: str):
    request = urllib.request.Request(url, headers={
        "User-Agent": "bhtdb-ai-reports-index",
        "Accept": "application/vnd.github+json",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def commits_for(path: str) -> list:
    """Every commit touching ``path``, newest first (paginated)."""
    commits, page = [], 1
    while True:
        batch = api(f"https://api.github.com/repos/{REPO}/commits"
                    f"?path={path}&per_page=100&page={page}")
        if not batch:
            return commits
        commits.extend(batch)
        if len(batch) < 100:
            return commits
        page += 1


def who(commit: dict) -> str:
    """GitHub login when the commit email maps to an account; otherwise the
    raw commit author name, stripped of stray quote characters."""
    author = commit.get("author") or {}
    if author.get("login"):
        return str(author["login"])
    name = ((commit.get("commit") or {}).get("author") or {}).get("name", "")
    return re.sub(r'[“”"‘’]', "", str(name)).strip()


def when(commit: dict) -> str:
    date = ((commit.get("commit") or {}).get("author") or {}).get("date", "")
    return str(date)[:10]  # ISO date is enough for display


def main() -> None:
    entries = {}
    rows = []
    for path in sorted((ROOT / "reports").glob("*.json")):
        report = json.loads(path.read_text(encoding="utf-8"))["report"]
        history = commits_for(f"reports/{path.name}")
        if not history:
            continue
        newest, oldest = history[0], history[-1]
        entries[path.name] = {
            "name": report.get("name", path.stem),
            "author": who(oldest),
            "created": when(oldest),
            "updated": when(newest),
            "updated_by": who(newest),
        }
        rows.append(
            f"| [{report.get('name', path.stem)}](reports/{path.name}) "
            f"| {len(report.get('sqls') or [])} "
            f"| @{who(oldest)} | {when(newest)} |")

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reports": entries,
    }
    (ROOT / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")

    table = "\n".join([
        "| Report | SQLs | Author | Last updated |",
        "|---|---|---|---|",
        *rows,
    ])
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    if TABLE_START in readme and TABLE_END in readme:
        pattern = re.compile(
            re.escape(TABLE_START) + ".*?" + re.escape(TABLE_END), re.S)
        readme = pattern.sub(f"{TABLE_START}\n{table}\n{TABLE_END}", readme)
        readme_path.write_text(readme, encoding="utf-8")
    print(f"indexed {len(entries)} report(s)")


if __name__ == "__main__":
    main()
