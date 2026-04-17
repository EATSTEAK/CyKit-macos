# Agent Instructions

## Environment management

- Use `uv` for environment and dependency management.
- Prefer `uv sync --extra test --extra docs` to prepare the local environment.
- Prefer `uv run pytest` for tests.
- Prefer `uv run sphinx-build -b html docs docs/_build/html` for documentation builds.
- Prefer `uv run python -m cykit ...` or `uv run python -c ...` for Python smoke checks.
- Avoid `pip install` and direct `python -m pip ...` flows unless `uv` is unavailable or broken in the current environment.
