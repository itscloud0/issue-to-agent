# Security

`issue-to-agent` reads local repository files and issue text to produce a local report. It does not call an LLM, upload code, or send issue contents to a hosted service.

## Safe Usage

- Review generated packs before pasting them into third-party tools.
- Do not include private secrets in issue files.
- Use GitHub issue URL input only with repositories you are allowed to access.
- Treat generated HTML as local output. Do not publish it if the issue or repo is private.

## Reporting Security Issues

Please do not open public issues for security problems. Email the maintainer or use GitHub private vulnerability reporting if the repository enables it.
