# SqawkPy Engineering (`eng`)

This folder contains engineering tools, specifications, plans, and CI automation guidelines for the SqawkPy project.

## Documents

- [**`IMPLEMENTATION_PLAN.md`**](IMPLEMENTATION_PLAN.md): Detailed architectural blueprint, 6-phase delivery roadmap, component mapping from .NET Polly v8, and pytest test suite mapping.
- **AI Coding Instructions**: Located in [`.github/instructions/`](../../.github/instructions), including [`python.instructions.md`](../../.github/instructions/python.instructions.md) ensuring Python idioms are prioritized over .NET constructs.
- **Specialized Agent Roles**: Located in [`.github/agents/`](../../.github/agents), outlining the agile outcome-based engineering team (Agile PM, Analysis, Design, Coding, Testing, Documentation).

## Developer Workflows

### Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r python/requirements.txt
pip install -e python
```

### Quality & Verification

```bash
# Run test suite
pytest python/test

# Run type checker
mypy python/src python/test

# Run linter & formatter
ruff check python
ruff format --check python

# Run benchmarks
pytest python/bench --benchmark-only
```

