from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from issue_to_agent.models import FileHit, Issue, RepositoryProfile
from issue_to_agent.pack import extract_acceptance_criteria, rank_files
from issue_to_agent.repo import scan_repository, tokenize


DEFAULT_FIXTURES = ROOT / "benchmark" / "fixtures" / "issues.json"
DEFAULT_RESULTS = ROOT / "benchmark" / "results.json"
DEFAULT_FAILURE_CASES = ROOT / "examples" / "failure-cases.md"
DEFAULT_CACHE = ROOT / "benchmark" / ".cache" / "repos"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark issue-to-agent against closed GitHub issues with known fixing PRs."
    )
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--repo-cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--failure-cases", type=Path, default=DEFAULT_FAILURE_CASES)
    parser.add_argument("--max-files", type=int, default=10)
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Use already cached repositories only; fail if a checkout is missing.",
    )
    args = parser.parse_args(argv)

    started = time.perf_counter()
    payload = json.loads(args.fixtures.read_text(encoding="utf-8"))
    fixtures = payload["fixtures"]
    cases: list[dict[str, Any]] = []

    for fixture in fixtures:
        repo_path = prepare_checkout(
            fixture=fixture,
            cache_root=args.repo_cache,
            no_fetch=args.no_fetch,
        )
        cases.append(evaluate_fixture(fixture, repo_path, max_files=args.max_files))

    results = {
        "schema_version": 1,
        "fixture_count": len(cases),
        "repository_count": len({case["repo"] for case in cases}),
        "languages": sorted({case["language"] for case in cases}),
        "duration_seconds": round(time.perf_counter() - started, 3),
        "tool": summarize(cases, prefix="tool"),
        "baseline": summarize(cases, prefix="baseline"),
        "comparisons": compare(cases),
        "cases": cases,
    }

    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    args.failure_cases.parent.mkdir(parents=True, exist_ok=True)
    args.failure_cases.write_text(render_failure_cases(results), encoding="utf-8")

    print(json.dumps(results["comparisons"], indent=2, sort_keys=True))
    return 0


def prepare_checkout(fixture: dict[str, Any], cache_root: Path, no_fetch: bool) -> Path:
    repo_key = fixture["repo"].replace("/", "__")
    repo_path = cache_root / repo_key
    cache_root.mkdir(parents=True, exist_ok=True)

    if not repo_path.exists():
        if no_fetch:
            raise SystemExit(f"missing cached repo for {fixture['repo']}: {repo_path}")
        run(["git", "clone", "--no-tags", fixture["repo_url"], str(repo_path)])

    if not no_fetch:
        run(["git", "-C", str(repo_path), "fetch", "--no-tags", "origin", fixture["pr_base_ref"]])

    run(["git", "-C", str(repo_path), "checkout", "--force", fixture["pr_base_ref"]])
    run(["git", "-C", str(repo_path), "clean", "-ffdqx"])
    return repo_path


def evaluate_fixture(
    fixture: dict[str, Any],
    repo_path: Path,
    max_files: int,
) -> dict[str, Any]:
    issue = Issue(
        title=fixture["issue_title"],
        body=fixture["issue_body"],
        source=fixture["issue_url"],
        url=fixture["issue_url"],
    )
    profile = scan_repository(repo_path)
    tool_hits = rank_files(issue, profile, max_files=max_files)
    baseline_hits = baseline_rank_files(issue, profile, max_files=max_files)
    expected_commands = fixture.get("expected_commands", [])
    expected_instruction_files = fixture.get("expected_instruction_files", [])
    detected_instruction_files = [item.path for item in profile.instructions]

    tool_paths = [hit.path for hit in tool_hits]
    baseline_paths = [hit.path for hit in baseline_hits]
    truth = fixture["changed_files"]

    case = {
        "id": fixture["id"],
        "repo": fixture["repo"],
        "language": fixture["language"],
        "issue_url": fixture["issue_url"],
        "closing_pr_url": fixture["closing_pr_url"],
        "base_ref": fixture["pr_base_ref"],
        "ground_truth_files": truth,
        "tool_top_files": tool_paths,
        "baseline_top_files": baseline_paths,
        "tool_top5_recall": recall_at(tool_paths, truth, 5),
        "tool_top10_recall": recall_at(tool_paths, truth, 10),
        "baseline_top5_recall": recall_at(baseline_paths, truth, 5),
        "baseline_top10_recall": recall_at(baseline_paths, truth, 10),
        "tool_irrelevant_file_rate": irrelevant_rate(tool_paths[:10], truth),
        "baseline_irrelevant_file_rate": irrelevant_rate(baseline_paths[:10], truth),
        "detected_commands": profile.commands,
        "expected_commands": expected_commands,
        "command_detection_pass": all(command in profile.commands for command in expected_commands),
        "detected_instruction_files": detected_instruction_files,
        "expected_instruction_files": expected_instruction_files,
        "agent_instruction_detection_pass": sorted(detected_instruction_files)
        == sorted(expected_instruction_files),
        "output_complete": output_complete(issue, profile, tool_hits),
    }
    return case


def baseline_rank_files(
    issue: Issue,
    profile: RepositoryProfile,
    max_files: int,
) -> list[FileHit]:
    issue_terms = set(tokenize(issue.title + "\n" + issue.body))
    hits: list[FileHit] = []
    for repo_file in profile.files:
        path_terms = set(tokenize(repo_file.path.replace("/", " ")))
        matches = sorted(issue_terms & path_terms)
        if not matches:
            continue
        score = len(matches) * 10
        hits.append(
            FileHit(
                path=repo_file.path,
                score=score,
                reasons=["filename matches: " + ", ".join(matches[:6])],
                snippets=[],
            )
        )

    hits.sort(key=lambda hit: (-hit.score, hit.path))
    return hits[:max_files]


def recall_at(paths: list[str], truth: list[str], limit: int) -> float:
    if not truth:
        return 0.0
    found = set(paths[:limit]) & set(truth)
    return round(len(found) / len(set(truth)), 4)


def irrelevant_rate(paths: list[str], truth: list[str]) -> float:
    if not paths:
        return 1.0
    irrelevant = [path for path in paths if path not in set(truth)]
    return round(len(irrelevant) / len(paths), 4)


def output_complete(
    issue: Issue,
    profile: RepositoryProfile,
    tool_hits: list[FileHit],
) -> bool:
    return all(
        [
            issue.title,
            tool_hits,
            profile.commands,
            extract_acceptance_criteria(issue),
        ]
    )


def summarize(cases: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    return {
        "mean_top5_recall": mean(case[f"{prefix}_top5_recall"] for case in cases),
        "mean_top10_recall": mean(case[f"{prefix}_top10_recall"] for case in cases),
        "mean_irrelevant_file_rate": mean(
            case[f"{prefix}_irrelevant_file_rate"] for case in cases
        ),
    }


def compare(cases: list[dict[str, Any]]) -> dict[str, Any]:
    top5_wins = sum(
        case["tool_top5_recall"] > case["baseline_top5_recall"] for case in cases
    )
    top10_wins = sum(
        case["tool_top10_recall"] > case["baseline_top10_recall"] for case in cases
    )
    return {
        "top5_cases_tool_beats_baseline": top5_wins,
        "top10_cases_tool_beats_baseline": top10_wins,
        "command_detection_accuracy": mean(
            1.0 if case["command_detection_pass"] else 0.0 for case in cases
        ),
        "agent_instruction_detection_accuracy": mean(
            1.0 if case["agent_instruction_detection_pass"] else 0.0 for case in cases
        ),
        "output_completeness_rate": mean(
            1.0 if case["output_complete"] else 0.0 for case in cases
        ),
    }


def mean(values: Any) -> float:
    return round(statistics.fmean(list(values)), 4)


def render_failure_cases(results: dict[str, Any]) -> str:
    lines = [
        "# Benchmark Failure Cases",
        "",
        "These cases come from `benchmark/results.json`. Ground truth is the changed-file list from the merged closing PR, so it is partial: a useful task pack may include nearby tests, docs, or config that were not changed in the PR.",
        "",
    ]
    failures = [
        case
        for case in results["cases"]
        if case["tool_top10_recall"] < 1.0 or not case["output_complete"]
    ]
    if not failures:
        lines.append("No failure cases in the latest benchmark run.")
        return "\n".join(lines) + "\n"

    for case in failures:
        missing = [
            path
            for path in case["ground_truth_files"]
            if path not in set(case["tool_top_files"][:10])
        ]
        lines.extend(
            [
                f"## {case['id']}",
                "",
                f"- Issue: {case['issue_url']}",
                f"- Closing PR: {case['closing_pr_url']}",
                f"- Top-10 recall: {case['tool_top10_recall']}",
                f"- Missing ground-truth files: {', '.join(missing) if missing else 'none'}",
                f"- Tool top files: {', '.join(case['tool_top_files']) if case['tool_top_files'] else 'none'}",
                f"- Baseline top files: {', '.join(case['baseline_top_files']) if case['baseline_top_files'] else 'none'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def run(command: list[str]) -> None:
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise SystemExit(f"command failed: {' '.join(command)}\n{detail}")


if __name__ == "__main__":
    raise SystemExit(main())
