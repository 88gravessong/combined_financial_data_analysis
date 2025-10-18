# Repository Guidelines

## Project Structure & Module Organization
- `app.py`: Flask app entry with UI endpoints.
- `analysis_multi.py`, `analysis_mal.py`: data processing/analysis routines.
- `sku_utils.py`: shared helpers and SKU utilities.
- `index.html`: frontend page served by Flask.
- `start.sh`: convenience script to launch the app.
- `requirements.txt`: Python dependencies.
- `.vscode/`: editor settings; `.gitignore` for repo hygiene.

## Build, Test, and Development Commands
- Create venv: `python3 -m venv .venv && source .venv/bin/activate`.
- Install deps: `pip install -r requirements.txt`.
- Run app (dev): `python app.py` or `./start.sh`.
- Lint (if installed): `ruff check .` and `black --check .`.

## Coding Style & Naming Conventions
- Python 3.9+; 4‑space indentation; UTF‑8.
- Function/variable names: `snake_case`; modules: `lower_snake_case.py`.
- Constants: `UPPER_SNAKE_CASE`; classes: `PascalCase`.
- Keep functions pure where possible; isolate I/O (file/network) at boundaries.
- Prefer `pathlib` over `os.path` and f‑strings over `%` formatting.
- Formatting: `black` (line length 100). Linting: `ruff` (configure via `pyproject.toml` if added).

## Testing Guidelines
- Framework: `pytest` (add to `requirements.txt` when tests are introduced).
- Place tests in `tests/` mirroring module names (e.g., `tests/test_sku_utils.py`).
- Name tests with `test_` prefix and arrange Given/When/Then comments.
- Run tests: `pytest -q`.

## Commit & Pull Request Guidelines
- Commit style: concise imperative subject (≤72 chars) and context in body.
  - Examples: `feat: add multi-country analysis params`, `fix: guard None SKU list`.
- One logical change per commit; include tests or sample data updates if relevant.
- PRs: include goal, summary of changes, how to run/verify, and screenshots for UI tweaks.
- Link related issues; request review; ensure CI (lint/tests) pass.

## Security & Configuration Tips
- Do not commit credentials or raw data files. Use `.env` (git-ignored) for secrets.
- Validate user inputs in `app.py`; sanitize file paths.
- Pin dependencies in `requirements.txt`; update via `pip-compile` if using `pip-tools`.

## Agent-Specific Instructions
- Obey this AGENTS.md for any edits within the repo.
- Keep changes minimal and localized; avoid unrelated refactors without discussion.
