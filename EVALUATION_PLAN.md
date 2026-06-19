# Evaluation Plan

## Central Claim

`issue-to-agent` should produce a more useful first handoff for a coding agent than a simple filename/path keyword baseline or manually copying an issue into an agent with no repository context.

## Primary Evaluation

Use closed GitHub issues with merged closing pull requests. Treat files changed by the closing PR as partial ground truth for useful implementation context.

Current benchmark fixture requirements:

- at least 15 closed issues
- at least 3 unrelated public repositories
- at least 2 programming-language ecosystems
- issues with identifiable closing pull requests
- actual changed files from those pull requests as partial ground truth

Current fixture set:

- `pallets/click` - Python
- `sindresorhus/ky` - TypeScript
- `BurntSushi/ripgrep` - Rust

## Metrics

File ranking:

- Top-5 file recall
- Top-10 file recall
- irrelevant-file rate

Task-pack quality:

- command-detection accuracy
- agent-instruction detection
- output completeness
- failure-case documentation

Project quality:

- clean install
- quickstart smoke
- unit tests
- benchmark reproducibility
- CI status
- safety scan

Adoption:

- repository views and unique viewers
- clones and unique cloners
- stars and forks
- external issues
- external pull requests
- release or package downloads when available
- independent mentions or usage reports

## Baseline

The benchmark compares against filename/path keyword matching. The baseline does not inspect file contents and does not produce a full task pack.

## Current Results

Latest benchmark: `BENCHMARK.md`, generated 2026-06-18.

| Metric | issue-to-agent | filename baseline |
| --- | ---: | ---: |
| Mean Top-5 file recall | 0.6444 | 0.3333 |
| Mean Top-10 file recall | 0.8889 | 0.3667 |
| Mean irrelevant-file rate | 0.8733 | 0.9304 |

Other current checks:

- Command detection accuracy: 1.0 on the fixture set.
- Agent-instruction detection accuracy: 1.0 for absence detection. The current fixture repos do not include expected instruction files, so this does not prove positive detection quality.
- Output completeness rate: 1.0 on the fixture set.

## Known Weaknesses

- Ranking is lexical, not semantic.
- High irrelevant-file rate remains because each issue returns up to 10 candidates while many closing PRs changed only one or two files.
- Changelog files are often changed by real PRs, but they are usually not the first useful implementation target.
- The benchmark uses PR-changed files as partial ground truth; useful nearby tests or configs may be marked irrelevant.
- Demand and adoption remain unproven until external usage evidence appears.

## Reproducible Commands

Run the benchmark:

```bash
python3 benchmark/run_benchmark.py
```

Use cached clones:

```bash
python3 benchmark/run_benchmark.py --no-fetch
```

Run local tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall src tests benchmark/run_benchmark.py
```

## Stop Or Reposition Criteria

Reposition or stop investing if any of these persist after the 14-day growth period:

- no external usage evidence after genuine distribution
- a simple prompt gives materially similar results for real issues
- the filename/path baseline catches up on key metrics
- real users mostly need broad repo packaging instead of issue-specific handoff
- ranking failures make generated task packs misleading
- the main value becomes packaging/integrations rather than measurable workflow improvement
