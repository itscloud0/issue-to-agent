from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Issue:
    title: str
    body: str
    source: str
    url: str = ""
    labels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "body": self.body,
            "source": self.source,
            "url": self.url,
            "labels": self.labels,
        }


@dataclass(frozen=True)
class AgentInstruction:
    path: str
    excerpt: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "excerpt": self.excerpt}


@dataclass(frozen=True)
class RepoFile:
    path: str
    absolute_path: Path
    text: str
    size: int


@dataclass(frozen=True)
class RepositoryProfile:
    root: Path
    instructions: list[AgentInstruction]
    commands: list[str]
    files: list[RepoFile]

    def to_dict(self) -> dict[str, object]:
        return {
            "root": str(self.root),
            "instructions": [instruction.to_dict() for instruction in self.instructions],
            "commands": self.commands,
            "file_count": len(self.files),
        }


@dataclass(frozen=True)
class FileHit:
    path: str
    score: int
    reasons: list[str]
    snippets: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "score": self.score,
            "reasons": self.reasons,
            "snippets": self.snippets,
        }


@dataclass(frozen=True)
class DiffContext:
    summary: str
    patch: str
    truncated: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary,
            "patch": self.patch,
            "truncated": self.truncated,
        }


@dataclass(frozen=True)
class TaskPack:
    issue: Issue
    repository: RepositoryProfile
    relevant_files: list[FileHit]
    acceptance_criteria: list[str]
    risks: list[str]
    prompt: str
    diff_context: DiffContext | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "issue": self.issue.to_dict(),
            "repository": self.repository.to_dict(),
            "relevant_files": [hit.to_dict() for hit in self.relevant_files],
            "acceptance_criteria": self.acceptance_criteria,
            "risks": self.risks,
            "prompt": self.prompt,
            "diff_context": (
                self.diff_context.to_dict() if self.diff_context is not None else None
            ),
        }
