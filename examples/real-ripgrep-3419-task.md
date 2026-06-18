# Issue Agent Pack

**Issue:** Title:

## Ready-To-Paste Agent Prompt

```text
Work as a pragmatic senior engineer in this repo.

Issue: Title:

Likely relevant files:
- crates/ignore/src/walk.rs (score 74): path matches: ignore, walk; content mentions: actual, applied, behavior, files, ignore, parallel, results, root
- crates/ignore/src/lib.rs (score 40): path matches: ignore; content mentions: description, files, ignore, rules, walk, walkbuilder
- crates/ignore/src/dir.rs (score 37): path matches: ignore; content mentions: applied, files, ignore, parallel, root, rules, walk
- crates/ignore/src/gitignore.rs (score 37): path matches: ignore; content mentions: actual, files, ignore, root, rules, walk
- crates/core/flags/hiargs.rs (score 33): content mentions: actual, behavior, files, ignore, multi, results, rules, threads
- crates/core/main.rs (score 29): content mentions: appears, applied, behavior, files, ignore, multi, parallel, rules
- crates/ignore/examples/walk.rs (score 28): path matches: ignore, walk; content mentions: ignore, parallel, threads, walkbuilder
- crates/ignore/tests/gitignore_matched_path_or_any_parents_tests.rs (score 28): path matches: ignore; content mentions: files, ignore, root; test file may need a regression case

Suggested commands:
- `cargo test`
- `cargo build`

Acceptance criteria:
- Resolve the behavior described by: Title:.
- Add or update the smallest relevant tests for the changed behavior.
- Run the suggested verification commands and report any command that cannot run.

Risks:
- No AGENTS.md or common agent instruction file was detected.

Keep the change minimal. Do not rewrite unrelated code. Verify before final response.
```

## Relevant Files

### `crates/ignore/src/walk.rs`
- Score: 74
- path matches: ignore, walk
- content mentions: actual, applied, behavior, files, ignore, parallel, results, root

```text
L19: dir::{Ignore, IgnoreBuilder},
L27: /// The error typically refers to a problem parsing ignore files in a
L79: /// Returns the depth at which this entry was created relative to the root.
```

### `crates/ignore/src/lib.rs`
- Score: 40
- path matches: ignore
- content mentions: description, files, ignore, rules, walk, walkbuilder

```text
L2: The ignore crate provides a fast recursive directory iterator that respects
L3: various filters such as globs, file types and `.gitignore` files. The precise
L4: matching rules and precedence is explained in the documentation for
```

### `crates/ignore/src/dir.rs`
- Score: 37
- path matches: ignore
- content mentions: applied, files, ignore, parallel, root, rules, walk

```text
L1: // This module provides a data structure, `Ignore`, that connects "directory
L2: // traversal" with "ignore matchers." Specifically, it knows about gitignore
L4: // Namely, every matcher logically corresponds to ignore rules from a single
```

### `crates/ignore/src/gitignore.rs`
- Score: 37
- path matches: ignore
- content mentions: actual, files, ignore, root, rules, walk

```text
L30: /// matched in one or more gitignore files.
L37: /// The actual glob string used to convert to a regex.
L38: actual: String,
```

### `crates/core/flags/hiargs.rs`
- Score: 33
- content mentions: actual, behavior, files, ignore, multi, results, rules, threads

```text
L57: globs: ignore::overrides::Override,
L61: ignore_file_case_insensitive: bool,
L62: ignore_file: Vec<PathBuf>,
```

### `crates/core/main.rs`
- Score: 29
- content mentions: appears, applied, behavior, files, ignore, multi, parallel, rules

```text
L7: use ignore::WalkState;
L26: // allocator, which appears to be substantially worse. (musl's goal is not to
L29: // heavy, musl's allocator appears to slow down ripgrep quite a bit. Therefore,
```

### `crates/ignore/examples/walk.rs`
- Score: 28
- path matches: ignore, walk
- content mentions: ignore, parallel, threads, walkbuilder

```text
L3: use {bstr::ByteVec, ignore::WalkBuilder, walkdir::WalkDir};
L7: let mut parallel = false;
L10: if path == "parallel" {
```

### `crates/ignore/tests/gitignore_matched_path_or_any_parents_tests.rs`
- Score: 28
- path matches: ignore
- content mentions: files, ignore, root
- test file may need a regression case

```text
L3: use ignore::gitignore::{Gitignore, GitignoreBuilder};
L5: const IGNORE_FILE: &'static str =
L9: let mut builder = GitignoreBuilder::new("ROOT");
```

## Suggested Commands

- `cargo test`
- `cargo build`

## Acceptance Criteria

- Resolve the behavior described by: Title:.
- Add or update the smallest relevant tests for the changed behavior.
- Run the suggested verification commands and report any command that cannot run.

## Risks

- No AGENTS.md or common agent instruction file was detected.

## Repo Instructions

No AGENTS.md, CLAUDE.md, or common editor instruction file detected.
