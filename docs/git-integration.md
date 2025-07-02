# Git Integration Guide

The Check Docs server provides powerful Git integration to analyze code changes and suggest documentation updates.

## How It Works

The `check_docs` tool:
1. Analyzes Git commit history
2. Identifies changed code files
3. Searches for related documentation
4. Suggests which docs need updates

## Basic Usage

### Check Recent Changes

Analyze changes from the last 7 days:

```python
results = await check_docs({
    "repo_path": "/path/to/your/repo",
    "since_days": 7
})
```

### Check Specific Commits

Analyze a specific range of commits:

```python
results = await check_docs({
    "repo_path": "/path/to/your/repo",
    "commit_range": "abc123..def456"
})
```

### Check Branch Differences

Compare branches to find what needs documenting:

```python
results = await check_docs({
    "repo_path": "/path/to/your/repo",
    "commit_range": "main..feature/new-api"
})
```

## Understanding Results

The tool returns:
- `total_code_changes`: Number of code files changed
- `documentation_suggestions`: List of docs that may need updates
- `affected_docs`: Documentation files referenced
- `relevance_score`: How closely the doc relates to the code change

## Best Practices

### 1. Regular Checks

Run documentation checks as part of your development workflow:
- Before creating pull requests
- After merging features
- As part of CI/CD pipelines

### 2. Meaningful Commit Messages

Good commit messages help the tool understand changes:
```bash
git commit -m "feat: Add user authentication to API endpoints"
```

### 3. Documentation Structure

Organize docs to match code structure:
```
src/
  auth/
    login.py
docs/
  auth/
    login.md
```

## Advanced Configuration

### Custom File Extensions

The tool checks common code extensions by default. Add more in `server.py`:

```python
code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.rb', '.php'}
```

### Ignore Patterns

Exclude certain files from analysis:

```python
ignored_patterns = ['test_', '_test.', '.spec.', 'mock']
code_changes = [f for f in diffs if not any(p in f for p in ignored_patterns)]
```

## Integration Examples

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "Checking documentation..."
uv run python -c "
import asyncio
from server import check_docs
result = asyncio.run(check_docs({'repo_path': '.', 'since_days': 1}))
if result['documentation_suggestions']:
    print('Documentation may need updates!')
"
```

### GitHub Actions

Add to `.github/workflows/docs-check.yml`:

```yaml
name: Check Documentation
on: [pull_request]

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Check docs
        run: |
          uv sync
          uv run python server.py check-docs --since-days=7
```