# Real-Repo Smoke Tests

Date: 2026-06-18

## Target 1

- Repository: `pallets/click`
- Clone URL: `https://github.com/pallets/click.git`
- Smoke commit: `8a1b1a3`
- Issue: https://github.com/pallets/click/issues/3571
- Issue title: ``click.progressbar` doesn't show full completion when using `show_pos=True` combined with `update_min_steps``

## Commands Run

`gh repo clone` first attempted SSH and failed because this machine has no usable GitHub SSH key. The smoke was rerun with HTTPS:

```bash
tmpdir=$(mktemp -d /tmp/issue-to-agent-click.XXXXXX)
git clone --depth 1 https://github.com/pallets/click.git "$tmpdir/repo"
python3 -m venv /tmp/issue-to-agent-real-venv
/tmp/issue-to-agent-real-venv/bin/python -m pip install .
/tmp/issue-to-agent-real-venv/bin/issue-to-agent pallets/click#3571 \
  --repo "$tmpdir/repo" \
  --output examples/real-click-3571-task.md
/tmp/issue-to-agent-real-venv/bin/issue-to-agent pallets/click#3571 \
  --repo "$tmpdir/repo" \
  --format html \
  --output demo/real-click-3571.html
```

## Generated Outputs

- Markdown task pack: `examples/real-click-3571-task.md`
- HTML report: `demo/real-click-3571.html`

## Output Summary

Top likely files from the generated task pack:

```text
- src/click/termui.py (score 43): content mentions: min, percentage, pos, progressbar, steps, terminal, time, update
- src/click/_termui_impl.py (score 39): content mentions: min, pos, progressbar, steps, terminal, time, update
- tests/test_termui.py (score 34): content mentions: isn, min, pos, progressbar, steps, time, update; test file may need a regression case
- tests/typing/typing_progressbar.py (score 21): path matches: progressbar; content mentions: progressbar; test file may need a regression case
```

Suggested commands:

```text
python -m pip install .
python -m pytest
python -m unittest discover -s tests
```

## Findings

- The smoke produced useful first-pass context: `src/click/termui.py`, `src/click/_termui_impl.py`, and `tests/test_termui.py` are plausible files for a `click.progressbar` bug.
- The first run exposed overly broad ranking terms that pushed `CHANGES.md` above source files. Ranking was tightened with repository-level common-term filtering, documentation/changelog penalties, and a broader stopword list.
- The final smoke output no longer ranks `CHANGES.md` above the implementation files.
- The repo has no `AGENTS.md`, `CLAUDE.md`, or common agent instruction file, so the risk section correctly calls that out.

## Not Verified

- The Click test suite was not run. This smoke validates task-pack generation, not the upstream bug fix.
- The generated task pack was not posted to GitHub.

## Target 2

- Repository: `sindresorhus/ky`
- Clone URL: `https://github.com/sindresorhus/ky.git`
- Smoke commit: `61d6d66`
- Issue: https://github.com/sindresorhus/ky/issues/863
- Issue title: `BeforeErrorHook: Property 'response' does not exist on type 'Error' (TypeScript issue)`

## Commands Run

```bash
tmpdir=$(mktemp -d /tmp/issue-to-agent-ky.XXXXXX)
git clone --depth 1 https://github.com/sindresorhus/ky.git "$tmpdir/repo"
python3 -m venv /tmp/issue-to-agent-node-venv
/tmp/issue-to-agent-node-venv/bin/python -m pip install .
/tmp/issue-to-agent-node-venv/bin/issue-to-agent sindresorhus/ky#863 \
  --repo "$tmpdir/repo" \
  --output examples/real-ky-863-task.md
/tmp/issue-to-agent-node-venv/bin/issue-to-agent sindresorhus/ky#863 \
  --repo "$tmpdir/repo" \
  --format html \
  --output demo/real-ky-863.html
```

## Generated Outputs

- Markdown task pack: `examples/real-ky-863-task.md`
- HTML report: `demo/real-ky-863.html`

## Output Summary

Top likely files from the generated task pack:

```text
- source/types/hooks.ts (score 10): content mentions: beforeerrorhook, beforeerrorstate
- source/index.ts (score 8): content mentions: beforeerrorhook, beforeerrorstate
```

Suggested commands:

```text
npm install
npm run test
npm run build
```

## Findings

- The first ky smoke exposed a real ranking weakness: generic issue-body terms such as `hello`, `got`, and `property` pushed `readme.md` and broad tests above the actual TypeScript hook definitions.
- Ranking was tightened by filtering generic issue prose, treating `readme.md` as documentation unless the issue asks for docs, and recognizing `source/` as an implementation tree.
- The final output ranks `source/types/hooks.ts` first, which is the credible starting point for the hook typing issue.
- The repo has no `AGENTS.md`, `CLAUDE.md`, or common agent instruction file, so the risk section correctly calls that out.

## Not Verified

- The ky test suite was not run. This smoke validates task-pack generation, not the upstream type fix.
- The generated task pack was not posted to GitHub.

## Target 3

- Repository: `BurntSushi/ripgrep`
- Clone URL: `https://github.com/BurntSushi/ripgrep.git`
- Issue: https://github.com/BurntSushi/ripgrep/issues/3419
- Issue title: `Nondeterminism in ignore::WalkBuilder parallel multi-root walk`

## Commands Run

issue-to-agent examples/issue-ripgrep-3419.md --repo ./ripgrep --output examples/real-ripgrep-3419-task.md

issue-to-agent examples/issue-ripgrep-3419.md --repo ./ripgrep --format html --output demo/real-ripgrep-3419.html

## Generated Outputs

- Markdown task pack: `examples/real-ripgrep-3419-task.md`
- HTML report: `demo/real-ripgrep-3419.html`

## Findings

- The ranking correctly surfaced `crates/ignore/src/walk.rs` as the top result.
- Additional ignore-related implementation files were ranked near the top.
- The generated task pack identified plausible verification commands (`cargo test`, `cargo build`).
- This provides a Rust real-repo smoke fixture demonstrating task-pack generation outside Python and TypeScript ecosystems.

## Not Verified

- Upstream tests were not executed.
- The upstream bug fix was not revalidated.