# Issue Agent Pack

**Issue:** BeforeErrorHook: Property 'response' does not exist on type 'Error' (TypeScript issue)
**URL:** https://github.com/sindresorhus/ky/issues/863

## Ready-To-Paste Agent Prompt

```text
Work as a pragmatic senior engineer in this repo.

Issue: BeforeErrorHook: Property 'response' does not exist on type 'Error' (TypeScript issue)
URL: https://github.com/sindresorhus/ky/issues/863

Likely relevant files:
- source/types/hooks.ts (score 10): content mentions: beforeerrorhook, beforeerrorstate
- source/index.ts (score 8): content mentions: beforeerrorhook, beforeerrorstate

Suggested commands:
- `npm install`
- `npm run test`
- `npm run build`

Acceptance criteria:
- Resolve the behavior described by: BeforeErrorHook: Property 'response' does not exist on type 'Error' (TypeScript issue).
- Add or update the smallest relevant tests for the changed behavior.
- Run the suggested verification commands and report any command that cannot run.

Risks:
- No AGENTS.md or common agent instruction file was detected.

Keep the change minimal. Do not rewrite unrelated code. Verify before final response.
```

## Relevant Files

### `source/types/hooks.ts`
- Score: 10
- content mentions: beforeerrorhook, beforeerrorstate

```text
L55: export type BeforeErrorState = {
L71: export type BeforeErrorHook = (state: BeforeErrorState) => Error | Promise<Error>;
L291: beforeError?: BeforeErrorHook[];
```

### `source/index.ts`
- Score: 8
- content mentions: beforeerrorhook, beforeerrorstate

```text
L57: BeforeErrorHook,
L58: BeforeErrorState,
```

## Suggested Commands

- `npm install`
- `npm run test`
- `npm run build`

## Acceptance Criteria

- Resolve the behavior described by: BeforeErrorHook: Property 'response' does not exist on type 'Error' (TypeScript issue).
- Add or update the smallest relevant tests for the changed behavior.
- Run the suggested verification commands and report any command that cannot run.

## Risks

- No AGENTS.md or common agent instruction file was detected.

## Repo Instructions

No AGENTS.md, CLAUDE.md, or common editor instruction file detected.
