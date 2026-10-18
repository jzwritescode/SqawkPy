---
applyTo: "**/*.md,python/docs/**,docs/**"
---

# Documentation

- User-facing behavior or API changes must update the relevant documentation under `python/docs/` or `docs/` (for example, `docs/strategies/retry.md` for retry changes).
- Code examples in documentation must be valid, idiomatic Python snippets with type annotations where appropriate. Keep examples testable (e.g. via doctest or automated snippet testing).
- Markdown is linted with markdownlint (`.markdownlint.json`).
- Do not edit `CHANGELOG.md` in feature PRs; it is updated as part of the release workflow.
- Do not edit benchmark reports or generated result files by hand.

