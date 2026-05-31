# Contributing to nodus-approvals

## Setup

```bash
git clone https://github.com/Masterplanner25/nodus-approvals.git
cd nodus-approvals
pip install -e ".[dev]"
```

## Running tests

```bash
pytest tests/ -q
```

## Code style

- Python 3.11+
- No required external dependencies (stdlib only)
- Type hints on all public functions

## Submitting changes

1. Fork the repo and create a branch from `main`
2. Add tests for any new behaviour
3. Ensure `pytest tests/ -q` passes
4. Open a pull request with a description of what changes and why
