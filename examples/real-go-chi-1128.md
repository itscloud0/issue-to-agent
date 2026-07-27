# Add explicit Router convenience method for HTTP QUERY

Following the standardization of the HTTP QUERY method in this accepted
[RFC](https://www.rfc-editor.org/info/rfc10008/) and the Go standard library
([golang/go#80058](https://github.com/golang/go/issues/80058) and [PR #80134](https://github.com/golang/go/issues/40243)),
I believe it would be good to add a native routing convenience wrapper for it
in chi.

Currently, chi features top-level wrappers for standard HTTP verbs (Get, Post,
Put, Patch, etc.). Adding a direct Query wrapper would continue to keep it
syntactically aligned.

I would be happy to raise a PR to implement this feature if the maintainers are
aligned as well.

Source: https://github.com/go-chi/chi/issues/1128
