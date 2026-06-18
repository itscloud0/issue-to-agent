from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .issue import load_issue
from .pack import build_task_pack
from .render import render_html, render_json, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="issue-to-agent",
        description="Turn a GitHub issue plus a local repo into a coding-agent task pack.",
    )
    parser.add_argument(
        "issue",
        help="Issue file, stdin '-', GitHub issue URL, or owner/repo#123.",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Local repository path to scan. Defaults to current directory.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "html"),
        default="markdown",
        help="Output format. Defaults to markdown.",
    )
    parser.add_argument(
        "--output",
        help="Write output to a file instead of stdout.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=8,
        help="Maximum relevant files to include. Defaults to 8.",
    )
    parser.add_argument(
        "--profile",
        choices=("codex", "claude", "cursor", "generic"),
        default="codex",
        help="Prompt style for the generated task pack. Defaults to codex.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.max_files < 1:
        parser.error("--max-files must be at least 1")

    try:
        issue = load_issue(args.issue)
        pack = build_task_pack(
            issue=issue,
            repo_root=args.repo,
            max_files=args.max_files,
            profile_name=args.profile,
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.format == "json":
        output = render_json(pack)
    elif args.format == "html":
        output = render_html(pack)
    else:
        output = render_markdown(pack)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
