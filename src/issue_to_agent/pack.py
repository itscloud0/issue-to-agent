from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .models import DiffContext, FileHit, Issue, RepoFile, RepositoryProfile, TaskPack
from .repo import collect_git_diff_context, scan_repository, tokenize

CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+(.+?)\s*$", re.MULTILINE)
DOTTED_EXTENSION_RE = re.compile(r"(?<![\w/])\.([A-Za-z0-9]{1,6})(?![A-Za-z0-9])")
DOTTED_CODE_REFERENCE_RE = re.compile(
    r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+\b"
)
SNAKE_IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9]*_[A-Za-z0-9_]*\b")
CAMEL_IDENTIFIER_RE = re.compile(r"\b[A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*\b")
UPPER_IDENTIFIER_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
LONG_OPTION_RE = re.compile(r"--[a-z][a-z0-9-]+")
RISK_TERMS = {"auth", "billing", "payment", "security", "secret", "token", "migration"}
GENERIC_CODE_REFERENCE_PARTS = {
    "codesandbox",
    "com",
    "github",
    "http",
    "https",
    "io",
    "main",
    "node_modules",
    "org",
    "source",
    "test",
    "tests",
}


def build_task_pack(
    issue: Issue,
    repo_root: str | Path,
    max_files: int = 8,
    profile_name: str = "codex",
    include_diff_context: bool = False,
    max_diff_chars: int = 12_000,
) -> TaskPack:
    repository = scan_repository(repo_root)
    relevant_files = rank_files(issue, repository, max_files=max_files)
    acceptance_criteria = extract_acceptance_criteria(issue)
    risks = detect_risks(issue, repository, relevant_files)
    diff_context = (
        collect_git_diff_context(repo_root, max_chars=max_diff_chars)
        if include_diff_context
        else None
    )
    prompt = render_agent_prompt(
        issue=issue,
        repository=repository,
        relevant_files=relevant_files,
        acceptance_criteria=acceptance_criteria,
        risks=risks,
        profile_name=profile_name,
        diff_context=diff_context,
    )
    return TaskPack(
        issue=issue,
        repository=repository,
        relevant_files=relevant_files,
        acceptance_criteria=acceptance_criteria,
        risks=risks,
        prompt=prompt,
        diff_context=diff_context,
    )


def rank_files(
    issue: Issue,
    repository: RepositoryProfile,
    max_files: int,
) -> list[FileHit]:
    issue_text = issue.title + "\n" + issue.body
    issue_terms = set(tokenize(issue_text))
    if not issue_terms:
        return []

    scoring_terms = select_scoring_terms(issue_terms, repository.files)
    scoring_terms.update(extract_signal_terms(issue))
    code_references = extract_code_references(issue)
    hits: list[FileHit] = []
    for repo_file in repository.files:
        hit = score_file(repo_file, scoring_terms, issue, code_references)
        if hit is not None:
            hits.append(hit)

    hits = boost_companion_file_hits(hits)
    hits.sort(key=lambda hit: (-hit.score, hit.path))
    return hits[:max_files]


def select_scoring_terms(issue_terms: set[str], files: list[RepoFile]) -> set[str]:
    document_frequency: Counter[str] = Counter()
    for repo_file in files:
        document_frequency.update(set(tokenize(repo_file.path + "\n" + repo_file.text)))

    common_threshold = max(8, len(files) // 4)
    scoring_terms = {
        term
        for term in issue_terms
        if document_frequency.get(term, 0) <= common_threshold
    }
    return scoring_terms or issue_terms


def score_file(
    repo_file: RepoFile,
    issue_terms: set[str],
    issue: Issue,
    code_references: set[str] | None = None,
) -> FileHit | None:
    path_lower = repo_file.path.lower().replace("_", " ")
    path_terms = set(tokenize(repo_file.path))
    content_tokens = Counter(tokenize(repo_file.text))

    path_matches = sorted(issue_terms & path_terms)
    content_matches = sorted(term for term in issue_terms if content_tokens.get(term, 0))
    references = extract_code_references(issue) if code_references is None else code_references
    code_reference_matches = find_code_reference_matches(
        repo_file, references
    )

    score = len(path_matches) * 12
    score += sum(min(content_tokens[term], 5) for term in content_matches)
    score += min(len(code_reference_matches) * 10, 30)
    has_term_match = score > 0

    issue_text = (issue.title + "\n" + issue.body).lower()
    if has_term_match and "test" in path_lower and any(
        term in issue_text for term in ("bug", "fail", "regression", "test", "expected")
    ):
        score += 8
    boost_reasons: list[str] = []
    if has_term_match and is_source_file_path(path_lower):
        score += 6
    if is_file_type_issue(issue_text) and "types" in path_terms:
        score += 16
        boost_reasons.append("file-type issue maps to a type registry")
    if has_term_match and "readme" in path_lower and any(
        term in issue_text for term in ("docs", "readme")
    ):
        score += 4
    if score > 0 and is_documentation_file(path_lower) and not any(
        term in issue_text for term in ("docs", "documentation", "readme")
    ):
        score -= 40
    if score > 0 and is_test_data_file(path_lower):
        score -= 25

    if score <= 0:
        return None

    reasons: list[str] = []
    if path_matches:
        reasons.append("path matches: " + ", ".join(path_matches[:6]))
    if code_reference_matches:
        reasons.append("code references: " + ", ".join(code_reference_matches[:6]))
    if content_matches:
        reasons.append("content mentions: " + ", ".join(content_matches[:8]))
    reasons.extend(boost_reasons)
    if "test" in path_lower:
        reasons.append("test file may need a regression case")

    return FileHit(
        path=repo_file.path,
        score=score,
        reasons=reasons,
        snippets=snippets_for_terms(repo_file.text, issue_terms),
    )


def snippets_for_terms(text: str, terms: set[str], limit: int = 3) -> list[str]:
    snippets: list[str] = []
    lowered_terms = {term.lower() for term in terms}
    for line_number, line in enumerate(text.splitlines(), start=1):
        if set(tokenize(line)) & lowered_terms:
            excerpt = line.strip()
            if len(excerpt) > 130:
                excerpt = excerpt[:127].rstrip() + "..."
            snippets.append(f"L{line_number}: {excerpt}")
            if len(snippets) >= limit:
                break
    return snippets


def extract_signal_terms(issue: Issue) -> set[str]:
    text = issue.title + "\n" + issue.body
    title_terms = set(tokenize(issue.title))
    terms = expand_term_variants(title_terms) - title_terms

    for pattern in (UPPER_IDENTIFIER_RE, LONG_OPTION_RE):
        for match in pattern.findall(text):
            terms.update(tokenize(match))

    for extension in DOTTED_EXTENSION_RE.findall(text):
        if len(extension) >= 2:
            terms.add(extension.lower())

    return terms


def extract_code_references(issue: Issue) -> set[str]:
    text = issue.title + "\n" + issue.body
    references: set[str] = set()

    for match in DOTTED_CODE_REFERENCE_RE.finditer(text):
        if match.start() > 0 and text[match.start() - 1] in "/:":
            continue

        normalized = match.group(0).lower()
        parts = [part.lower() for part in match.group(0).split(".")]
        if any(part in {"com", "io", "org", "net"} for part in parts):
            continue
        if any(is_code_reference_part(part) for part in parts):
            references.add(normalized)
        references.update(part for part in parts if is_code_reference_part(part))

    for pattern in (SNAKE_IDENTIFIER_RE, CAMEL_IDENTIFIER_RE, UPPER_IDENTIFIER_RE):
        for match in pattern.findall(text):
            normalized = match.lower()
            if is_code_reference_part(normalized):
                references.add(normalized)

    return references


def is_code_reference_part(value: str) -> bool:
    return (
        len(value) >= 4
        and value not in {"true", "false", "none", "null"}
        and value not in GENERIC_CODE_REFERENCE_PARTS
    )


def find_code_reference_matches(repo_file: RepoFile, references: set[str]) -> list[str]:
    if not references:
        return []

    haystack = (repo_file.path + "\n" + repo_file.text).lower()
    return sorted(reference for reference in references if reference in haystack)


def boost_companion_file_hits(hits: list[FileHit]) -> list[FileHit]:
    groups: dict[str, list[FileHit]] = {}
    for hit in hits:
        key = companion_file_key(hit.path)
        if key is None:
            continue
        groups.setdefault(key, []).append(hit)

    boosts: dict[str, int] = {}
    for group in groups.values():
        has_test = any(is_test_file_path(hit.path) for hit in group)
        has_source = any(
            is_source_file_path(hit.path.lower().replace("_", " ")) for hit in group
        )
        if not has_test or not has_source:
            continue

        strongest_score = max(hit.score for hit in group)
        if strongest_score < 30:
            continue

        for hit in group:
            boosts[hit.path] = max(
                boosts.get(hit.path, 0), min(24, strongest_score // 2)
            )

    if not boosts:
        return hits

    boosted_hits: list[FileHit] = []
    for hit in hits:
        boost = boosts.get(hit.path, 0)
        if not boost:
            boosted_hits.append(hit)
            continue
        boosted_hits.append(
            FileHit(
                path=hit.path,
                score=hit.score + boost,
                reasons=hit.reasons + ["paired source/test file"],
                snippets=hit.snippets,
            )
        )
    return boosted_hits


def companion_file_key(path: str) -> str | None:
    name = Path(path).name.lower()
    if "." not in name:
        return None

    stem = name.split(".", 1)[0]
    for prefix in ("test_",):
        if stem.startswith(prefix):
            stem = stem[len(prefix) :]
    for suffix in ("_test",):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]

    if stem in {"__init__", "index", "main", "test", "tests"}:
        return None
    return stem


def is_test_file_path(path: str) -> bool:
    path_lower = path.lower()
    parts = path_lower.split("/")
    name = parts[-1]
    stem = name.split(".", 1)[0]
    return (
        "tests" in parts
        or "test" in parts
        or "__tests__" in parts
        or stem.startswith("test_")
        or stem.endswith("_test")
        or ".test." in name
        or ".spec." in name
    )


def expand_term_variants(terms: set[str]) -> set[str]:
    expanded = set(terms)
    for term in terms:
        candidates: list[str] = []
        if len(term) > 5 and term.endswith("ies"):
            candidates.append(term[:-3] + "y")
        if len(term) > 5 and term.endswith("ing"):
            candidates.append(term[:-3])
        if len(term) > 4 and term.endswith("ed"):
            candidates.append(term[:-2])
        if len(term) > 4 and term.endswith("es"):
            candidates.append(term[:-2])
        if len(term) > 4 and term.endswith("s") and not term.endswith("ss"):
            candidates.append(term[:-1])
        for candidate in candidates:
            expanded.update(tokenize(candidate))
    return expanded


def is_source_file_path(path_lower: str) -> bool:
    return any(
        term in path_lower
        for term in ("src/", "source/", "lib/", "app/", "crates/")
    )


def is_file_type_issue(issue_text: str) -> bool:
    return (
        "file type" in issue_text
        or "file types" in issue_text
        or "extension" in issue_text
        or "extensions" in issue_text
    )


def is_documentation_file(path_lower: str) -> bool:
    return (
        path_lower == "changes.md"
        or path_lower == "changelog.md"
        or path_lower == "faq.md"
        or path_lower == "guide.md"
        or path_lower == "readme.md"
        or path_lower.startswith(".github/issue_template/")
        or path_lower.startswith(".github/pull_request_template")
        or path_lower.startswith("docs/")
        or path_lower.startswith("doc/")
    )


def is_test_data_file(path_lower: str) -> bool:
    return (
        path_lower.startswith("tests/data/")
        or path_lower.startswith("testdata/")
        or "/testdata/" in path_lower
    )


def extract_acceptance_criteria(issue: Issue) -> list[str]:
    explicit = [
        match.strip()
        for match in CHECKBOX_RE.findall(issue.body)
        if not is_template_confirmation_checkbox(match)
    ]
    if explicit:
        return explicit

    return [
        f"Resolve the behavior described by: {issue.title}.",
        "Add or update the smallest relevant tests for the changed behavior.",
        "Run the suggested verification commands and report any command that cannot run.",
    ]


def is_template_confirmation_checkbox(text: str) -> bool:
    normalized = " ".join(text.lower().strip(" .").split())
    return (
        normalized == "i have a different issue"
        or normalized.startswith("i have searched")
        or normalized.startswith("i have read")
        or normalized.startswith("i have reviewed")
        or normalized.startswith("i confirm")
        or normalized.startswith("i agree")
    )


def detect_risks(
    issue: Issue,
    repository: RepositoryProfile,
    relevant_files: list[FileHit],
) -> list[str]:
    risks: list[str] = []
    issue_terms = set(tokenize(issue.title + "\n" + issue.body))
    sensitive_terms = sorted(issue_terms & RISK_TERMS)
    if sensitive_terms:
        risks.append(
            "Sensitive area mentioned: "
            + ", ".join(sensitive_terms)
            + ". Avoid broad auth, billing, migration, or secret-handling changes."
        )
    if not relevant_files:
        risks.append(
            "No relevant files were found. Start with repo search before editing."
        )
    if not repository.commands:
        risks.append(
            "No install/test commands were detected. Inspect project docs before running changes."
        )
    if not repository.instructions:
        risks.append("No AGENTS.md or common agent instruction file was detected.")
    return risks


def render_agent_prompt(
    issue: Issue,
    repository: RepositoryProfile,
    relevant_files: list[FileHit],
    acceptance_criteria: list[str],
    risks: list[str],
    profile_name: str,
    diff_context: DiffContext | None = None,
) -> str:
    profile = profile_name.lower()
    intro = {
        "codex": "Work as a pragmatic senior engineer in this repo.",
        "claude": "Work carefully in this repo and keep the diff scoped.",
        "cursor": "Use the existing project patterns and keep edits minimal.",
        "generic": "Work in this repo and solve the issue with a focused diff.",
    }.get(profile, "Work in this repo and solve the issue with a focused diff.")

    lines = [
        intro,
        "",
        f"Issue: {issue.title}",
    ]
    if issue.url:
        lines.append(f"URL: {issue.url}")
    if issue.labels:
        lines.append("Labels: " + ", ".join(issue.labels))

    lines.extend(["", "Likely relevant files:"])
    if relevant_files:
        for hit in relevant_files:
            lines.append(f"- {hit.path} (score {hit.score}): {'; '.join(hit.reasons)}")
    else:
        lines.append("- None detected. Search the repo before editing.")

    lines.extend(["", "Suggested commands:"])
    if repository.commands:
        lines.extend(f"- `{command}`" for command in repository.commands)
    else:
        lines.append("- Inspect README/package metadata for install and test commands.")

    if diff_context is not None:
        lines.extend(["", "Current tracked git diff context:"])
        lines.append(diff_context.summary)
        if diff_context.patch:
            lines.extend(["```diff", diff_context.patch.rstrip(), "```"])
        if diff_context.truncated:
            lines.append("Inspect the local git diff before editing; this patch was truncated.")

    lines.extend(["", "Acceptance criteria:"])
    lines.extend(f"- {criterion}" for criterion in acceptance_criteria)

    if risks:
        lines.extend(["", "Risks:"])
        lines.extend(f"- {risk}" for risk in risks)

    if repository.instructions:
        lines.extend(["", "Repo instructions to honor:"])
        for instruction in repository.instructions:
            lines.append(f"- {instruction.path}: {instruction.excerpt}")

    lines.extend(
        [
            "",
            "Keep the change minimal. Do not rewrite unrelated code. Verify before final response.",
        ]
    )
    return "\n".join(lines).strip() + "\n"
