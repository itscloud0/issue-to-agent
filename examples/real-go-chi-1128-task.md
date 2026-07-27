# Issue Agent Pack

**Issue:** Add explicit Router convenience method for HTTP QUERY

## Ready-To-Paste Agent Prompt

```text
Work as a pragmatic senior engineer in this repo.

Issue: Add explicit Router convenience method for HTTP QUERY

Likely relevant files:
- mux.go (score 40): code references: query; content mentions: continue, http, library, patch, post, put, query, routing
- mux_test.go (score 39): code references: query; content mentions: accepted, direct, http, info, patch, post, put, query; test file may need a regression case
- _examples/rest/main.go (score 36): code references: query; content mentions: etc, good, http, implement, level, post, put, query
- chi.go (score 29): code references: query; content mentions: http, info, patch, post, put, query, routing, standard
- tree.go (score 29): code references: query; content mentions: continue, http, keep, query, rfc, routing
- middleware/compress.go (score 27): content mentions: accepted, adding, http, level, org, post, put, rfc
- middleware/strip_test.go (score 24): code references: query; content mentions: http, keep, level, query, top; test file may need a regression case
- README.md (score 20): code references: query; content mentions: accepted, direct, etc, explicit, features, golang, good, happy

Suggested commands:
- `go test ./...`
- `make test`

Acceptance criteria:
- Resolve the behavior described by: Add explicit Router convenience method for HTTP QUERY.
- Add or update the smallest relevant tests for the changed behavior.
- Run the suggested verification commands and report any command that cannot run.

Risks:
- No AGENTS.md or common agent instruction file was detected.

Keep the change minimal. Do not rewrite unrelated code. Verify before final response.
```

## Relevant Files

### `mux.go`
- Score: 40
- code references: query
- content mentions: continue, http, library, patch, post, put, query, routing

```text
L6: "net/http"
L13: // Mux is a simple HTTP route multiplexer that parses a request path,
L15: // the http.Handler interface and is friendly with the standard library.
```

### `mux_test.go`
- Score: 39
- code references: query
- content mentions: accepted, direct, http, info, patch, post, put, query
- test file may need a regression case

```text
L9: "net/http"
L10: "net/http/httptest"
L18: countermw := func(next http.Handler) http.Handler {
```

### `_examples/rest/main.go`
- Score: 36
- code references: query
- content mentions: etc, good, http, implement, level, post, put, query

```text
L1: // This example demonstrates a HTTP REST web service with some fixture data.
L13: //	$ curl http://localhost:3333/
L16: //	$ curl http://localhost:3333/articles
```

### `chi.go`
- Score: 29
- code references: query
- content mentions: http, info, patch, post, put, query, routing, standard

```text
L1: // Package chi is a small, idiomatic and composable router for building HTTP services.
L10: //		"net/http"
L21: //		r.Get("/", func(w http.ResponseWriter, r *http.Request) {
```

### `tree.go`
- Score: 29
- code references: query
- content mentions: continue, http, keep, query, rfc, routing

```text
L5: // (MIT licensed). It's been heavily modified for use as a HTTP routing tree.
L9: "net/http"
L36: // methodQuery is the HTTP QUERY method (RFC 10008), a safe, idempotent
```

### `middleware/compress.go`
- Score: 27
- content mentions: accepted, adding, http, level, org, post, put, rfc

```text
L11: "net/http"
L34: // compression level.
L38: // your handler you should set w.Header().Set("Content-Type", http.DetectContentType(yourBody))
```

### `middleware/strip_test.go`
- Score: 24
- code references: query
- content mentions: http, keep, level, query, top
- test file may need a regression case

```text
L4: "net/http"
L5: "net/http/httptest"
L16: // This middleware must be mounted at the top level of the router, not at the end-handler
```

### `README.md`
- Score: 20
- code references: query
- content mentions: accepted, direct, etc, explicit, features, golang, good, happy

```text
L6: `chi` is a lightweight, idiomatic and composable router for building Go HTTP services. It's
L7: especially good at helping you write large REST API services that are kept maintainable as your
L15: The key considerations of chi's design are: project structure, maintainability, standard http
```

## Suggested Commands

- `go test ./...`
- `make test`

## Acceptance Criteria

- Resolve the behavior described by: Add explicit Router convenience method for HTTP QUERY.
- Add or update the smallest relevant tests for the changed behavior.
- Run the suggested verification commands and report any command that cannot run.

## Risks

- No AGENTS.md or common agent instruction file was detected.

## Repo Instructions

No AGENTS.md, CLAUDE.md, or common editor instruction file detected.
