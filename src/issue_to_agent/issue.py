from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TextIO

from .models import Issue

GITHUB_ISSUE_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/issues/(?P<number>\d+)"
)
GITHUB_ISSUE_SHORT_RE = re.compile(
    r"^(?P<owner>[^/\s#]+)/(?P<repo>[^/\s#]+)#(?P<number>\d+)$"
)


def load_issue(source: str, stdin: TextIO | None = None) -> Issue:
    """Load issue text from a file, stdin, or GitHub issue reference."""
    if source == "-":
        text = (stdin or sys.stdin).read()
        if not text.strip():
            raise ValueError("stdin did not contain issue text")
        return parse_issue_text(text, source="stdin")

    github_ref = parse_github_issue_ref(source)
    if github_ref is not None:
        return fetch_github_issue(*github_ref, source=source)

    path = Path(source)
    if path.exists():
        if not path.is_file():
            raise ValueError(f"issue source is not a file: {source}")
        return parse_issue_text(path.read_text(encoding="utf-8"), source=str(path))

    if "\n" in source:
        return parse_issue_text(source, source="literal")

    raise ValueError(
        "issue source must be a file, stdin '-', GitHub issue URL, or owner/repo#123"
    )


def parse_issue_text(text: str, source: str) -> Issue:
    lines = [line.rstrip() for line in text.strip().splitlines()]
    if not lines:
        raise ValueError("issue text is empty")

    first = next((line for line in lines if line.strip()), "")
    title = first.lstrip("# ").strip()
    if not title:
        title = "Untitled issue"
    if len(title) > 140:
        title = title[:137].rstrip() + "..."

    body_lines = lines[1:] if first == lines[0] else lines
    body = "\n".join(body_lines).strip()
    return Issue(title=title, body=body, source=source)


def parse_github_issue_ref(source: str) -> tuple[str, str, str] | None:
    match = GITHUB_ISSUE_URL_RE.match(source)
    if match:
        return match.group("owner"), match.group("repo"), match.group("number")

    match = GITHUB_ISSUE_SHORT_RE.match(source)
    if match:
        return match.group("owner"), match.group("repo"), match.group("number")
    return None


def fetch_github_issue(owner: str, repo: str, number: str, source: str) -> Issue:
    command = [
        "gh",
        "issue",
        "view",
        number,
        "--repo",
        f"{owner}/{repo}",
        "--json",
        "title,body,labels,url",
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise ValueError(
            "GitHub issue input requires the gh CLI. Use a pasted issue file instead."
        ) from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise ValueError(f"gh issue view failed for {owner}/{repo}#{number}: {detail}")

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("gh issue view returned invalid JSON") from exc

    labels = [
        str(label.get("name", ""))
        for label in payload.get("labels", [])
        if isinstance(label, dict) and label.get("name")
    ]
    return Issue(
        title=str(payload.get("title") or f"{owner}/{repo}#{number}"),
        body=str(payload.get("body") or ""),
        source=source,
        url=str(payload.get("url") or ""),
        labels=labels,
    )
