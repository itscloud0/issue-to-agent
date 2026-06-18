# Benchmark

This benchmark checks whether `issue-to-agent` finds files that were actually changed by merged pull requests that closed real GitHub issues.

## Fixture Set

- 15 closed GitHub issues.
- 3 unrelated public repositories.
- 3 ecosystems: Python, TypeScript, Rust.
- Each fixture records the issue URL, closing PR URL, PR base commit, and changed files from the closing PR.
- Fixtures live in `benchmark/fixtures/issues.json`.

Repositories:

- `pallets/click`
- `sindresorhus/ky`
- `BurntSushi/ripgrep`

## Run

```bash
python3 benchmark/run_benchmark.py
```

The first run clones public repositories into `benchmark/.cache/`. The script checks out each PR base commit, scans files, and writes:

- `benchmark/results.json`
- `examples/failure-cases.md`

Use cached repositories only:

```bash
python3 benchmark/run_benchmark.py --no-fetch
```

## Baseline

The comparison baseline ranks files using only issue keywords matched against filenames and paths. It does not inspect file contents.

## Latest Results

Generated on 2026-06-18.

| Metric | issue-to-agent | filename baseline |
| --- | ---: | ---: |
| Mean Top-5 file recall | 0.6444 | 0.3333 |
| Mean Top-10 file recall | 0.8889 | 0.3667 |
| Mean irrelevant-file rate | 0.8733 | 0.9304 |

Other checks:

- Command detection accuracy: 1.0.
- Agent-instruction detection accuracy: 1.0 for this fixture set; all benchmarked repos had no expected instruction files, so this only verifies correct absence detection.
- Output completeness rate: 1.0.

## Interpretation

`issue-to-agent` beats the simple filename baseline on mean Top-5 and Top-10 recall, and it produces complete task packs for all fixtures. The result supports continuing the project, but it is not strong enough to claim robust file localization.

Known weak spots:

- Some implementation files are still ranked below nearby tests or broad framework files when the issue uses behavior-level language instead of concrete API names.
- Changelog files are commonly part of real PRs but usually not helpful for an agent's first implementation step.
- The irrelevant-file rate is high because each issue returns up to 10 candidates while many PRs changed only one or two files.

See `examples/failure-cases.md` for concrete misses.
