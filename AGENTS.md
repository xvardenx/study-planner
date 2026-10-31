# Repo Rules and Guidelines

## README Project Description

**Do not** make changes to the project description and requirements section of the README.

## Code Guidelines

### Python

Use `uv` for dependency management and running project commands. Keep runtime
dependencies in `[project.dependencies]` and development tools in
`[dependency-groups].dev` in `pyproject.toml`. Commit `uv.lock` for reproducible
environments.

After the initial `uv sync`, install the repository hooks:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

Run all commit-stage checks manually with `uv run pre-commit run --all-files`.
Run pre-push checks manually with
`uv run pre-commit run --all-files --hook-stage pre-push`. Keep the Ruff version
in the development dependencies and `.pre-commit-config.yaml` synchronized.

Include docstrings for all non-trivial functions that explain what the function
does. For more complex functions that require more thorough explanations, use a
Google-style docstring format when needed.

Always run the commands below after making code changes.

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
```

Do not commit Google OAuth client secrets, access tokens, refresh tokens, or
other credentials. Store local credentials only in ignored files or outside the
repository.
