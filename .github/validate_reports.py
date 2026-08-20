"""Validate every report in reports/ — run by CI on pull requests and on
pushes to main, so a broken or conflicting report never lands.

Checks:
  1. Valid report envelope (schema_version 1, kind "report", non-empty name,
     at least one SQL).
  2. Report names are unique across the repository (case-insensitive). The
     name is the identity BHTDB.ai uses to detect updates: two files sharing
     a name would silently overwrite each other on the user's machine.
  3. Each SQL is a single SELECT/WITH statement (lexical check). This is a
     courtesy gate for reviewers — BHTDB.ai enforces read-only for real, in
     code, at run time.

Exits non-zero with one line per problem.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_COMMENT = re.compile(r"--[^\n]*|/\*.*?\*/", re.S)


def sql_problem(sql: str) -> str | None:
    stripped = _COMMENT.sub(" ", sql or "").strip()
    if not stripped:
        return "empty SQL"
    first = stripped.split(None, 1)[0].upper()
    if first not in ("SELECT", "WITH"):
        return f"must start with SELECT/WITH (found {first})"
    body = stripped.rstrip().rstrip(";")
    # A remaining ';' inside string literals is legal SQL, so only flag a ';'
    # outside quotes: one statement per SQL entry.
    in_string = False
    for ch in body:
        if ch == "'":
            in_string = not in_string
        elif ch == ";" and not in_string:
            return "must be a single statement (found ';' mid-text)"
    return None


def main() -> int:
    problems: list[str] = []
    names: dict[str, str] = {}  # normalized name -> file that claimed it
    for path in sorted((ROOT / "reports").glob("*.json")):
        label = f"reports/{path.name}"
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{label}: not valid JSON ({exc})")
            continue
        if not isinstance(envelope, dict) \
                or envelope.get("kind") != "report" \
                or envelope.get("schema_version") != 1 \
                or not isinstance(envelope.get("report"), dict):
            problems.append(f"{label}: not a schema_version-1 report envelope")
            continue
        report = envelope["report"]
        name = str(report.get("name", "")).strip()
        if not name:
            problems.append(f"{label}: report has no name")
            continue
        key = name.casefold()
        if key in names:
            problems.append(
                f"{label}: report name “{name}” is already used by "
                f"{names[key]} — names are the app's update identity and must "
                "be unique; please rename one of them")
        else:
            names[key] = label
        sqls = report.get("sqls") or []
        if not sqls:
            problems.append(f"{label}: report has no SQLs")
        for i, entry in enumerate(sqls, 1):
            if not isinstance(entry, dict):
                problems.append(f"{label}: SQL #{i} is not an object")
                continue
            if not str(entry.get("name", "")).strip():
                problems.append(f"{label}: SQL #{i} has no name")
            problem = sql_problem(str(entry.get("sql", "")))
            if problem:
                problems.append(f"{label}: SQL #{i} "
                                f"({entry.get('name', '?')}): {problem}")

    for line in problems:
        print(f"ERROR: {line}")
    if not problems:
        print(f"OK: {len(names)} report(s), all names unique, all SQLs "
              "lexically read-only")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
