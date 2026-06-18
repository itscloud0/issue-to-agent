# Contributing

Thanks for considering a contribution.

## Local Setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests
```

## Development Notes

- Keep the core local-first and deterministic.
- Do not add LLM calls to the default path.
- Add tests for ranking, command detection, and renderer changes.
- Keep example repos small but realistic.
- Prefer clear error messages over broad exception handling.

## Pull Requests

Before opening a PR, run:

```bash
python -m unittest discover -s tests
issue-to-agent examples/issue-checkout-timeout.md --repo examples/mini-repo
issue-to-agent examples/issue-checkout-timeout.md --repo examples/mini-repo --format json --output /tmp/issue-agent-pack.json
python -m json.tool /tmp/issue-agent-pack.json
python -m compileall src tests
```
