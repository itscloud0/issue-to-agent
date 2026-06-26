from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .models import AgentInstruction, DiffContext, RepoFile, RepositoryProfile

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".turbo",
    "target",
}

SPECIAL_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "Makefile",
    "justfile",
    "Dockerfile",
    "pyproject.toml",
    "package.json",
    "tsconfig.json",
    "go.mod",
    "Cargo.toml",
}

TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".rb",
    ".php",
    ".cs",
    ".swift",
    ".kt",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ini",
    ".cfg",
    ".txt",
    ".sh",
    ".sql",
    ".prisma",
    ".proto",
}

STOPWORDS = {
    "about",
    "add",
    "after",
    "also",
    "and",
    "are",
    "bar",
    "because",
    "before",
    "being",
    "but",
    "can",
    "cannot",
    "combined",
    "could",
    "data",
    "default",
    "does",
    "doesn",
    "doesnt",
    "error",
    "expected",
    "exist",
    "exists",
    "everyone",
    "end",
    "final",
    "for",
    "from",
    "full",
    "got",
    "guess",
    "have",
    "hello",
    "import",
    "inside",
    "into",
    "issue",
    "length",
    "range",
    "object",
    "property",
    "running",
    "seen",
    "show",
    "return",
    "should",
    "that",
    "the",
    "their",
    "there",
    "this",
    "trying",
    "type",
    "typed",
    "typescript",
    "using",
    "use",
    "way",
    "will",
    "when",
    "with",
    "would",
    "wrong",
}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")
MAX_FILE_BYTES = 120_000
DEFAULT_MAX_DIFF_CHARS = 12_000


def scan_repository(repo_root: str | Path) -> RepositoryProfile:
    root = Path(repo_root).resolve()
    if not root.exists():
        raise ValueError(f"repo path does not exist: {repo_root}")
    if not root.is_dir():
        raise ValueError(f"repo path is not a directory: {repo_root}")

    files = list(iter_repo_files(root))
    return RepositoryProfile(
        root=root,
        instructions=discover_instructions(root),
        commands=detect_commands(root),
        files=files,
    )


def collect_git_diff_context(
    repo_root: str | Path,
    max_chars: int = DEFAULT_MAX_DIFF_CHARS,
) -> DiffContext:
    if max_chars < 1:
        raise ValueError("--max-diff-chars must be at least 1")

    root = Path(repo_root).resolve()
    work_tree = git_output(root, ["rev-parse", "--is-inside-work-tree"])
    if work_tree is None or work_tree.returncode != 0 or work_tree.stdout.strip() != "true":
        return DiffContext(
            summary="Git diff unavailable: repo is not inside a git work tree.",
            patch="",
        )

    has_head = git_output(root, ["rev-parse", "--verify", "HEAD"])
    if has_head is not None and has_head.returncode == 0:
        pathspec = ["HEAD", "--", "."]
    else:
        pathspec = ["--", "."]

    stat = git_output(
        root,
        ["diff", "--no-ext-diff", "--no-color", "--stat", *pathspec],
    )
    patch = git_output(
        root,
        [
            "diff",
            "--no-ext-diff",
            "--no-color",
            "--find-renames",
            "--unified=3",
            *pathspec,
        ],
    )
    if stat is None or patch is None:
        return DiffContext(summary="Git diff unavailable: git command failed.", patch="")

    if stat.returncode != 0 or patch.returncode != 0:
        detail = (stat.stderr or patch.stderr).strip().splitlines()
        suffix = f" {detail[0]}" if detail else ""
        return DiffContext(summary=f"Git diff unavailable:{suffix}".strip(), patch="")

    patch_text = patch.stdout.strip()
    truncated = len(patch_text) > max_chars
    if truncated:
        patch_text = patch_text[:max_chars].rstrip() + "\n[diff truncated]"

    return DiffContext(
        summary=stat.stdout.strip() or "No tracked git diff detected.",
        patch=patch_text,
        truncated=truncated,
    )


def git_output(root: Path, args: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError:
        return None


def iter_repo_files(root: Path) -> list[RepoFile]:
    results: list[RepoFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if not is_text_candidate(path):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > MAX_FILE_BYTES:
            continue
        text = read_text(path)
        if text is None:
            continue
        results.append(
            RepoFile(
                path=path.relative_to(root).as_posix(),
                absolute_path=path,
                text=text,
                size=size,
            )
        )
    return results


def is_text_candidate(path: Path) -> bool:
    if path.name in SPECIAL_FILES:
        return True
    return path.suffix in TEXT_SUFFIXES


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    except OSError:
        return None


def discover_instructions(root: Path) -> list[AgentInstruction]:
    candidates = [
        root / "AGENTS.md",
        root / "CLAUDE.md",
        root / ".github" / "copilot-instructions.md",
        root / ".cursor" / "rules",
    ]
    instructions: list[AgentInstruction] = []
    for path in candidates:
        if path.is_file():
            text = read_text(path) or ""
            excerpt = compact_excerpt(text, limit=700)
            instructions.append(
                AgentInstruction(path=path.relative_to(root).as_posix(), excerpt=excerpt)
            )
    return instructions


def detect_commands(root: Path) -> list[str]:
    commands: list[str] = []

    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        pyproject_text = read_text(pyproject) or ""
        commands.append("python -m pip install .")
        if "pytest" in pyproject_text.lower():
            commands.append("python -m pytest")
        if (root / "tests").is_dir():
            commands.append("python -m unittest discover -s tests")

    package_json = root / "package.json"
    if package_json.is_file():
        commands.append("npm install")
        commands.extend(detect_npm_script_commands(package_json))

    if (root / "go.mod").is_file():
        commands.append("go test ./...")

    if (root / "Cargo.toml").is_file():
        commands.append("cargo test")
        commands.append("cargo build")

    makefile = root / "Makefile"
    if makefile.is_file():
        commands.extend(detect_make_targets(makefile, prefix="make"))

    justfile = root / "justfile"
    if justfile.is_file():
        commands.extend(detect_make_targets(justfile, prefix="just"))

    commands.extend(detect_tox_commands(root))
    commands.extend(detect_nox_commands(root))
    commands.extend(detect_uv_commands(root))
    return dedupe(commands)


def detect_npm_script_commands(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    scripts = payload.get("scripts", {})
    if not isinstance(scripts, dict):
        return []

    preferred = ["test", "lint", "typecheck", "build"]
    return [f"npm run {name}" for name in preferred if name in scripts]


def detect_make_targets(path: Path, prefix: str) -> list[str]:
    text = read_text(path) or ""
    commands: list[str] = []
    for name in ("test", "lint", "check", "build"):
        if re.search(rf"^{re.escape(name)}\s*:", text, flags=re.MULTILINE):
            commands.append(f"{prefix} {name}")
    return commands


def detect_tox_commands(root: Path) -> list[str]:
    tox_ini = root / "tox.ini"
    if tox_ini.is_file():
        text = read_text(tox_ini) or ""
        if re.search(r"(?m)^\s*\[tox\]\s*$", text):
            return ["tox"]
    return []


def detect_nox_commands(root: Path) -> list[str]:
    if (root / "noxfile.py").is_file():
        text = read_text(root / "noxfile.py") or ""
        if text.strip():
            return ["nox"]
    return []


def detect_uv_commands(root: Path) -> list[str]:
    commands: list[str] = []
    pyproject = root / "pyproject.toml"
    pyproject_text = read_text(pyproject) or "" if pyproject.is_file() else ""
    has_uv = (root / "uv.lock").is_file() or re.search(
        r"(?m)^\s*\[tool\.uv\]\s*$", pyproject_text
    )
    if has_uv:
        commands.append("uv sync")
        if "pytest" in pyproject_text.lower():
            commands.append("uv run pytest")
        elif (root / "tests").is_dir():
            commands.append("uv run python -m unittest discover -s tests")
    return commands


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in WORD_RE.findall(text.lower().replace("_", " ")):
        if raw in STOPWORDS:
            continue
        if len(raw) < 3:
            continue
        tokens.append(raw)
    return tokens


def compact_excerpt(text: str, limit: int) -> str:
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
