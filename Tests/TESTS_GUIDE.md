# Pytest Setup and CI/CD Integration

## Local Testing

### Installation

Install development dependencies including pytest:

```bash
pip install -e ".[dev]"
```

### Running Tests

Run all tests:

```bash
pytest
```

Run tests with coverage report:

```bash
pytest --cov=jsweb --cov-report=html
```

Run specific test file:

```bash
pytest Tests/test_routing.py -v
```

Run tests with specific marker:

```bash
pytest -m unit
pytest -m integration
pytest -m slow
```

Run tests matching a pattern:

```bash
pytest -k "test_form" -v
```

### Available Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.forms` - Form validation tests
- `@pytest.mark.routing` - Routing tests
- `@pytest.mark.database` - Database tests
- `@pytest.mark.security` - Security tests

### Coverage Reports

After running tests with `--cov`, view the HTML coverage report:

```bash
# On Windows
start htmlcov/index.html

# On Linux/Mac
open htmlcov/index.html
```

## CI/CD Integration

### GitHub Actions Workflow

The project includes a GitHub Actions workflow (`.github/workflows/tests.yml`) that:

1. **Tests Job** - Runs tests on multiple Python versions (3.8-3.12)
   - Installs dependencies
   - Runs pytest with coverage
   - Uploads coverage to Codecov
   - Archives coverage reports as artifacts

2. **Lint Job** - Checks code quality
   - Black (code formatting)
   - isort (import sorting)
   - Flake8 (linting)
   - MyPy (type checking)

3. **Security Job** - Scans for security issues
   - Bandit (security analysis)
   - Safety (dependency vulnerabilities)

### Workflow Triggers

The workflow runs automatically on:

- Push to `main` and `develop` branches
- Pull requests to `main` and `develop` branches

### Codecov Integration

Coverage reports are automatically uploaded to Codecov. Add a `CODECOV_TOKEN` secret in your GitHub repository settings for authenticated uploads (optional).

## Configuration Files

### pytest.ini

Main pytest configuration file with:
- Test discovery patterns
- Output options
- Test markers
- Asyncio mode settings

### pyproject.toml

Contains additional pytest and coverage configuration:
- `[tool.pytest.ini_options]` - Pytest settings
- `[tool.coverage.run]` - Coverage collection settings
- `[tool.coverage.report]` - Coverage report options

### .coveragerc

Detailed coverage configuration:
- Source paths
- Files to omit
- Excluded lines
- Report formats

## Pre-commit Hooks

To run tests and linting before commits, set up pre-commit:

```bash
pre-commit install
pre-commit run --all-files
```

The `.pre-commit-config.yaml` should include pytest and other linting tools.

## Tips for Writing Tests

### Basic Test Structure

```python
import pytest
from jsweb import App

@pytest.mark.unit
def test_app_creation():
    """Test that an app can be created."""
    app = App(__name__)
    assert app is not None
```

### Using Fixtures

```python
@pytest.mark.unit
def test_with_app(app):
    """Test using the app fixture."""
    assert app is not None

@pytest.mark.unit
def test_with_config(config):
    """Test using the config fixture."""
    assert config.TESTING is True
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async code."""
    result = await some_async_function()
    assert result is not None
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test", "test"),
    ("TEST", "test"),
    ("Test", "test"),
])
def test_string_lowercase(input, expected):
    """Test string lowercasing with multiple inputs."""
    assert input.lower() == expected
```

## Troubleshooting

### ImportError: No module named 'jsweb'

Install the package in development mode:

```bash
pip install -e .
```

### Coverage not showing results

Make sure to use:

```bash
pytest --cov=jsweb
```

### Tests not being discovered

Check that test files follow the pattern: `test_*.py` and test functions start with `test_`

### Async test issues

Ensure pytest-asyncio is installed:

```bash
pip install pytest-asyncio
```
