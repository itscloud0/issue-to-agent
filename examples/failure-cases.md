# Benchmark Failure Cases

These cases come from `benchmark/results.json`. Ground truth is the changed-file list from the merged closing PR, so it is partial: a useful task pack may include nearby tests, docs, or config that were not changed in the PR.

## pallets-click-3164

- Issue: https://github.com/pallets/click/issues/3164
- Closing PR: https://github.com/pallets/click/pull/3186
- Top-10 recall: 0.5
- Missing ground-truth files: CHANGES.rst
- Tool top files: src/click/_termui_impl.py, src/click/termui.py, tests/test_termui.py, src/click/shell_completion.py, src/click/types.py, tests/test_utils.py, src/click/utils.py, src/click/_compat.py, src/click/testing.py, src/click/_winconsole.py
- Baseline top files: src/click/_termui_impl.py, src/click/shell_completion.py, src/click/termui.py, .devcontainer/on-create-command.sh, docs/click-concepts.md, docs/command-line-reference.md, docs/extending-click.md, docs/shell-completion.md, examples/termui/pyproject.toml, examples/termui/termui.py

## pallets-click-3105

- Issue: https://github.com/pallets/click/issues/3105
- Closing PR: https://github.com/pallets/click/pull/3211
- Top-10 recall: 0.3333
- Missing ground-truth files: CHANGES.rst, tests/test_types.py
- Tool top files: src/click/types.py, tests/test_options.py, src/click/utils.py, tests/test_arguments.py, tests/test_info_dict.py, src/click/termui.py, src/click/_termui_impl.py, src/click/parser.py, tests/test_termui.py, src/click/testing.py
- Baseline top files: tests/test_info_dict.py, .devcontainer/on-create-command.sh, tests/test_command_decorators.py, tests/test_context.py, tests/test_parser.py, docs/command-line-reference.md, docs/documentation.md, docs/parameter-types.md, docs/why.md, examples/complex/complex/__init__.py

## pallets-click-3360

- Issue: https://github.com/pallets/click/issues/3360
- Closing PR: https://github.com/pallets/click/pull/3434
- Top-10 recall: 0.3333
- Missing ground-truth files: CHANGES.rst, src/click/formatting.py
- Tool top files: tests/test_options.py, tests/test_termui.py, tests/test_formatting.py, src/click/testing.py, tests/test_arguments.py, src/click/termui.py, tests/test_commands.py, tests/test_utils.py, src/click/types.py, tests/test_context.py
- Baseline top files: .github/ISSUE_TEMPLATE/bug-report.md, docs/arguments.md, docs/click-concepts.md, docs/command-line-reference.md, docs/commands-and-groups.md, docs/commands.md, docs/extending-click.md, examples/complex/complex/cli.py, examples/complex/complex/commands/__init__.py, examples/complex/complex/commands/cmd_init.py

## pallets-click-3043

- Issue: https://github.com/pallets/click/issues/3043
- Closing PR: https://github.com/pallets/click/pull/3126
- Top-10 recall: 0.5
- Missing ground-truth files: .gitignore, CHANGES.rst
- Tool top files: src/click/shell_completion.py, tests/test_options.py, tests/test_shell_completion.py, src/click/types.py, src/click/termui.py, docs/shell-completion.md, tests/test_termui.py, src/click/_termui_impl.py, docs/advanced.md, tests/test_commands.py
- Baseline top files: src/click/shell_completion.py, src/click/types.py, tests/test_shell_completion.py, .github/ISSUE_TEMPLATE/bug-report.md, .github/ISSUE_TEMPLATE/config.yml, .github/ISSUE_TEMPLATE/feature-request.md, .github/pull_request_template.md, docs/command-line-reference.md, docs/shell-completion.md, src/click/__init__.py
