"""The labels that tell the two versions of an amended article apart (one format, read
and written here only).

law.go.kr statutes carry an amendment not yet in force right after the article in force
(ingest/parse.py mark_versions). The parser labels the headings:

    "제18조의3(난임치료휴가) [2026. 11. 27. 시행]"            the amended version
    "제18조의3(난임치료휴가) [개정 전, 2026. 11. 27. 전까지]"   the version before it

The labels hold dates only; which version is in force is decided with today's date
when answering (agent/answer.py) and in the UI (frontend/src/versions.jsx, same format).
"""

import datetime as dt
import re

RE_AMENDED = re.compile(r"\s*\[(\d{4})\. (\d{1,2})\. (\d{1,2})\. 시행\]$")
RE_BEFORE = re.compile(r"\s*\[개정 전, (\d{4})\. (\d{1,2})\. (\d{1,2})\. 전까지\]$")


def amended(heading: str, date: str) -> str:
    """date as the statute writes it: "2026. 11. 27." """
    return f"{heading} [{date} 시행]"


def before(heading: str, date: str) -> str:
    return f"{heading} [개정 전, {date} 전까지]"


def parse(heading: str) -> tuple[str, str | None, dt.date | None]:
    """(heading without the label, "amended" | "before" | None, the effective date)."""
    for rx, kind in ((RE_AMENDED, "amended"), (RE_BEFORE, "before")):
        m = rx.search(heading or "")
        if m:
            return heading[: m.start()], kind, dt.date(*map(int, m.groups()))
    return heading or "", None, None
