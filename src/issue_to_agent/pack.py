from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .models import FileHit, Issue, RepoFile, RepositoryProfile, TaskPack
from .repo import scan_repository, tokenize

CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+(.+?)\s*$", re.MULTILINE)
RISK_TERMS = {"auth", "billing", "payment", "security", "secret", "token", "migration"}


def build_task_pack(
    issue: Issue,
    repo_root: str | Path,
    max_files: int = 8,
    profile_name: str = "codex",
) -> TaskPack:
    repository = scan_repository(repo_root)
    relevant_files = rank_files(issue, repository, max_files=max_files)
    acceptance_criteria = extract_acceptance_criteria(issue)
    risks = detect_risks(issue, repository, relevant_files)
    prompt = render_agent_prompt(
        issue=issue,
        repository=repository,
        relevant_files=relevant_files,
        acceptance_criteria=acceptance_criteria,
        risks=risks,
        profile_name=profile_name,
    )
    return TaskPack(
        issue=issue,
        repository=repository,
        relevant_files=relevant_files,
        acceptance_criteria=acceptance_criteria,
        risks=risks,
        prompt=prompt,
    )


def rank_files(
    issue: Issue,
    repository: RepositoryProfile,
    max_files: int,
) -> list[FileHit]:
    issue_terms = set(tokenize(issue.title + "\n" + issue.body))
    if not issue_terms:
        return []

    scoring_terms = select_scoring_terms(issue_terms, repository.files)
    hits: list[FileHit] = []
    for repo_file in repository.files:
        hit = score_file(repo_file, scoring_terms, issue)
        if hit is not None:
            hits.append(hit)

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


def score_file(repo_file: RepoFile, issue_terms: set[str], issue: Issue) -> FileHit | None:
    path_lower = repo_file.path.lower().replace("_", " ")
    path_terms = set(tokenize(repo_file.path))
    content_tokens = Counter(tokenize(repo_file.text))

    path_matches = sorted(issue_terms & path_terms)
    content_matches = sorted(term for term in issue_terms if content_tokens.get(term, 0))

    score = len(path_matches) * 8
    score += sum(min(content_tokens[term], 5) for term in content_matches)
    if score <= 0:
        return None

    issue_text = (issue.title + "\n" + issue.body).lower()
    if "test" in path_lower and any(
        term in issue_text for term in ("bug", "fail", "regression", "test", "expected")
    ):
        score += 8
    if any(term in path_lower for term in ("src/", "source/", "lib/", "app/")):
        score += 6
    if "readme" in path_lower and any(term in issue_text for term in ("docs", "readme")):
        score += 4
    if is_documentation_file(path_lower) and not any(
        term in issue_text for term in ("docs", "documentation", "readme")
    ):
        score -= 40

    if score <= 0:
        return None

    reasons: list[str] = []
    if path_matches:
        reasons.append("path matches: " + ", ".join(path_matches[:6]))
    if content_matches:
        reasons.append("content mentions: " + ", ".join(content_matches[:8]))
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


def is_documentation_file(path_lower: str) -> bool:
    return (
        path_lower == "changes.md"
        or path_lower == "changelog.md"
        or path_lower == "readme.md"
        or path_lower.startswith("docs/")
        or path_lower.startswith("doc/")
    )


def extract_acceptance_criteria(issue: Issue) -> list[str]:
    explicit = [match.strip() for match in CHECKBOX_RE.findall(issue.body)]
    if explicit:
        return explicit

    return [
        f"Resolve the behavior described by: {issue.title}.",
        "Add or update the smallest relevant tests for the changed behavior.",
        "Run the suggested verification commands and report any command that cannot run.",
    ]


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
