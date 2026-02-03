# Contributing

Thanks for your interest in contributing. This repository supports an academic project with a structured sprint cadence, so changes should be scoped, documented, and reviewed.

## Quick Start
1. Create a feature branch from `main` using `feature/<topic>` or `fix/<issue>`.
2. Keep changes focused and include tests or evidence where applicable.
3. Update documentation when behavior or configuration changes.

## Development Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Tests
```bash
pytest
```

## Pull Requests
Include the following in each PR:
- Summary of changes
- Test results or rationale if not run
- Screenshots for dashboard/UI changes

## Data and Secrets
- Do not commit raw data or processed outputs.
- Never commit credentials or `.env` files.
