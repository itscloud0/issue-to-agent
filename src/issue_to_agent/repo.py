from __future__ import annotations

import json
import re
import subprocess
from fnmatch import fnmatch
from pathlib import Path

from .models import (
    AgentInstruction,
    DiffContext,
    ProjectConfig,
    RepoFile,
    RepositoryProfile,
)

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
CONFIG_FILE_NAMES = (".issue-to-agent.json", "issue-to-agent.json")


def scan_repository(
    repo_root: str | Path,
    config_path: str | Path | None = None,
) -> RepositoryProfile:
    root = Path(repo_root).resolve()
    if not root.exists():
        raise ValueError(f"repo path does not exist: {repo_root}")
    if not root.is_dir():
        raise ValueError(f"repo path is not a directory: {repo_root}")

    config = load_project_config(root, config_path)
    files = list(iter_repo_files(root, ignored_paths=config.ignored_paths))
    return RepositoryProfile(
        root=root,
        instructions=discover_instructions(root),
        commands=apply_command_preferences(
            detect_commands(root),
            config.command_preferences,
        ),
        files=files,
        config=config,
    )


def load_project_config(
    repo_root: Path,
    config_path: str | Path | None = None,
) -> ProjectConfig:
    path = resolve_config_path(repo_root, config_path)
    if path is None:
        return ProjectConfig()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid issue-to-agent config JSON at {path}: {exc.msg}") from exc
    except OSError as exc:
        raise ValueError(f"could not read issue-to-agent config at {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"issue-to-agent config must be a JSON object: {path}")

    return ProjectConfig(
        source=path.relative_to(repo_root).as_posix()
        if path.is_relative_to(repo_root)
        else str(path),
        ignored_paths=read_string_list(payload, "ignored_paths", path),
        command_preferences=read_string_list(payload, "command_preferences", path),
        ranking_boosts=read_ranking_boosts(payload, path),
    )


def resolve_config_path(
    repo_root: Path,
    config_path: str | Path | None,
) -> Path | None:
    if config_path:
        path = Path(config_path)
        if not path.is_absolute():
            path = repo_root / path
        if not path.is_file():
            raise ValueError(f"issue-to-agent config file does not exist: {path}")
        return path.resolve()

    for name in CONFIG_FILE_NAMES:
        path = repo_root / name
        if path.is_file():
            return path
    return None


def read_string_list(payload: dict[str, object], key: str, path: Path) -> list[str]:
    value = payload.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings in {path}")
    return [item.strip() for item in value if item.strip()]


def read_ranking_boosts(payload: dict[str, object], path: Path) -> dict[str, int]:
    value = payload.get("ranking_boosts", {})
    if not isinstance(value, dict):
        raise ValueError(f"ranking_boosts must be an object in {path}")

    boosts: dict[str, int] = {}
    for pattern, boost in value.items():
        if not isinstance(pattern, str) or not pattern.strip():
            raise ValueError(f"ranking_boosts keys must be non-empty strings in {path}")
        if not isinstance(boost, int) or isinstance(boost, bool) or boost < 0:
            raise ValueError(
                f"ranking_boosts values must be non-negative integers in {path}"
            )
        boosts[pattern.strip()] = boost
    return boosts


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


def iter_repo_files(
    root: Path,
    ignored_paths: list[str] | None = None,
) -> list[RepoFile]:
    ignored_paths = ignored_paths or []
    results: list[RepoFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root).as_posix()
        relative_parts = path.relative_to(root).parts
        if any(part in EXCLUDED_DIRS for part in relative_parts):
            continue
        if any(matches_path_pattern(relative_path, pattern) for pattern in ignored_paths):
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


def apply_command_preferences(
    commands: list[str],
    command_preferences: list[str],
) -> list[str]:
    if not command_preferences:
        return commands
    return dedupe(command_preferences + commands)


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


def matches_path_pattern(path: str, pattern: str) -> bool:
    normalized_pattern = pattern.strip().lstrip("./")
    if not normalized_pattern:
        return False
    normalized_path = path.lstrip("./")
    if normalized_pattern.endswith("/"):
        return normalized_path.startswith(normalized_pattern)
    if "/" not in normalized_pattern:
        parts = normalized_path.split("/")
        return fnmatch(normalized_path, normalized_pattern) or any(
            fnmatch(part, normalized_pattern) for part in parts
        )
    return fnmatch(normalized_path, normalized_pattern)
