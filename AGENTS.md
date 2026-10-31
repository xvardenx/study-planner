# Repo Rules and Guidelines

## README Project Description

**Do not** make changes to the project description and requirements section of the README.

## Code Guidelines

### Python

Include doc-strings for all non-trival functions that explain what the function does. For more complex functions that require more thorough explanations used a Google style doc-string format, only if needed.

Always run the below commands after making code changes.

```bash
uv run ruff format .
uv run ruff check .
```
