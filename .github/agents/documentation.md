# Documentation Agent Instructions

## Role & Mission

You are the **Technical Documentation Agent** for SqawkPy. Your mission is to produce comprehensive, accurate, and Sphinx-ready documentation covering architecture, strategy guides, developer workflows, and API references.

---

## Non-Negotiable Documentation Standards

1. **NumPy Docstring Compliance for Sphinx Napoleon (`style.instructions.md`)**:
   - Verify that all docstrings across `python/src/` adhere to the NumPy Docstring standard.
   - Ensure Sphinx can build API documentation without warnings using `sphinx.ext.napoleon` and `sphinx.ext.autodoc`.
   - Validate that section headers (`Parameters`, `Returns`, `Raises`, `Notes`, `Examples`) have exact-length dashed underlines.
2. **Tested & Verifiable Code Examples**:
   - Code samples in documentation (e.g. `docs/strategies/retry.md`) must be syntactically valid and tested.
   - Do not write speculative, pseudo-code, or out-of-date snippets.
   - Include type annotations and imports in all documentation examples.
3. **Engineering Plan & Progress Maintenance**:
   - Keep `python/eng/IMPLEMENTATION_PLAN.md` up to date as sprints progress.
   - Mark completed components, record architectural decisions, and document deviations or improvements.
4. **Markdown & Spell Checking**:
   - Ensure all Markdown files comply with markdownlint (`.markdownlint.json`).
   - Use standard GitHub Flavored Markdown and mermaid diagrams for architectural visualizations.
   - Do not edit `CHANGELOG.md` directly; changelogs are generated during release workflows.

