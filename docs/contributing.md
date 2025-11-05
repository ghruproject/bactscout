# Contributing to BactScout

Thank you for your interest in contributing to BactScout! This guide explains how to get started.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. All contributors are expected to treat each other with respect.

## How to Contribute

### Reporting Issues

Found a bug or have a feature request?

1. **Check existing issues**: Search [GitHub Issues](https://github.com/nfareed/bactscout/issues) first
2. **Create new issue** with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - System information (OS, Python version)
   - BactScout version: `pixi run bactscout --version`

### Submitting Code

#### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/bactscout.git
cd bactscout

# Add upstream remote
git remote add upstream https://github.com/nfareed/bactscout.git
```

#### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

Use descriptive branch names.

#### 3. Set Up Development Environment

```bash
# Install development dependencies
pixi install

# Verify tests pass
pixi run test
```

#### 4. Make Changes

Follow code style:
- **Python**: PEP 8 (use black for formatting)
- **Docstrings**: Use triple quotes and describe parameters
- **Type hints**: Add type annotations to new functions

Example:
```python
def extract_sample_name(filename: str) -> str:
    """Extract sample name from FASTQ filename.
    
    Args:
        filename: Path or name of FASTQ file
        
    Returns:
        Cleaned sample identifier
        
    Example:
        >>> extract_sample_name("sample_001_R1.fastq.gz")
        "sample_001"
    """
    # Implementation
    pass
```

#### 5. Write/Update Tests

- Add tests for new functionality
- Update tests if you change existing behavior
- Ensure all tests pass: `pixi run test`
- Aim for >80% code coverage

```bash
# Run tests with coverage
pixi run pytest tests/ --cov=bactscout --cov-report=html

# Check coverage report
open htmlcov/index.html
```


#### 6. Update Documentation

- Update README.md if behavior changes
- Update docstrings
- Add entries to CHANGELOG.md
- Update relevant docs/ files

#### 7. Commit Changes

```bash
git add .
git commit -m "Type: Brief description

Longer explanation if needed.

Fixes #issue_number (if applicable)
"
```

**Commit types**:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code formatting (no logic change)
- `refactor:` Code restructuring
- `test:` Test additions/updates
- `chore:` Maintenance tasks

#### 8. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to related issues: "Fixes #123"
- Summary of changes
- Any breaking changes noted

#### 9. Respond to Review

- Maintainers will review your PR
- Address feedback in new commits
- Push updates: `git push origin feature/your-feature-name`
- Discussion continues until approved

#### 10. Merge

Once approved:
- PR will be squashed and merged
- Your branch can be deleted
- Changes available in next release

## Development Setup

### Full Setup

```bash
# Clone repository
git clone https://github.com/nfareed/bactscout.git
cd bactscout

# Install all dependencies
pixi install

# Verify setup
pixi run test
pixi run bactscout --version
```

### Run Development Tasks

```bash
# Run all tests
pixi run test

# Run specific test file
pixi run pytest tests/test_fastp.py -v

# Run tests with coverage
pixi run pytest --cov=bactscout

# Format code
pixi run black bactscout/ tests/

# Run linting
pixi run flake8 bactscout/ tests/

# Run type checking
pixi run mypy bactscout/
```

### Project Structure

```
bactscout/
├── __init__.py          # Package initialization
├── __version__.py       # Version string
├── main.py              # Pipeline logic
├── thread.py            # Sample processing
├── preflight.py         # Input validation
├── util.py              # Utilities
└── summary.py           # Report generation

bactscout.py             # CLI entry point

tests/
├── test_fastp.py        # Fastp extraction tests (56)
├── test_stringmlst.py   # MLST typing tests (13)
├── test_main.py         # Pipeline tests (4)
├── test_file_pairs.py   # FASTQ discovery tests (10)
└── test_bactscout_cli.py # CLI tests (16)

docs/                    # Documentation files
├── index.md
├── getting-started/
├── usage/
├── guide/
├── reference/
└── development/

pixi.toml               # Pixi dependencies & tasks
pyproject.toml          # Python package config
.github/                # GitHub workflows
docker/                 # Docker configuration
```

## Areas for Contribution

### Code Improvements

- Optimize performance
- Improve error messages
- Add type hints
- Refactor complex functions
- Add logging

### New Features

- Support new species/schemes
- Add quality metrics
- Improve reporting
- Add visualization
- Extend analysis tools

### Documentation

- Fix typos
- Improve clarity
- Add examples
- Add tutorials
- Improve API docs

### Testing

- Increase coverage
- Add edge case tests
- Test error conditions
- Performance tests
- Integration tests

### Infrastructure

- CI/CD improvements
- Docker optimization
- Packaging improvements
- Release automation

## Code Style Guidelines

### Python Style (PEP 8)

```python
# Good
def calculate_coverage(total_bases: int, ref_size: float) -> float:
    """Calculate coverage from total bases and reference size."""
    return total_bases / (ref_size * 1_000_000)

# Bad
def calc_cov(tb, rs):
    return tb / (rs * 1000000)
```

### Naming Conventions

```python
# Classes: PascalCase
class QualityMetrics:
    pass

# Functions/variables: snake_case
def extract_sample_name():
    pass
sample_count = 0

# Constants: UPPER_SNAKE_CASE
MAX_COVERAGE = 100
DEFAULT_THREADS = 2

# Private: leading underscore
def _internal_function():
    pass
```

### Docstring Format

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description on first line.
    
    Longer description can go here, explaining
    the function behavior in detail.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When invalid input provided
        
    Example:
        >>> result = function_name("test", 5)
        >>> result
        True
    """
```

### Import Organization

```python
# Standard library
import os
from pathlib import Path
from typing import Optional

# Third-party
import pandas as pd
from rich.console import Console

# Local
from bactscout.util import extract_sample_name
```

## Testing Guidelines

### Test File Organization

```python
# tests/test_module.py
import pytest
from bactscout.module import function_to_test

class TestFunctionName:
    """Tests for function_to_test."""
    
    def test_basic_operation(self):
        """Test basic functionality."""
        result = function_to_test(input)
        assert result == expected
    
    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
    
    @pytest.mark.parametrize("input,expected", [
        ("case1", "result1"),
        ("case2", "result2"),
    ])
    def test_multiple_cases(self, input, expected):
        """Test various input cases."""
        assert function_to_test(input) == expected
```

### Coverage Requirements

- Aim for 80%+ coverage of new code
- 100% coverage of critical paths
- Use `pytest --cov` to check

```bash
pixi run pytest --cov=bactscout --cov-report=html
open htmlcov/index.html
```

## Git Workflow

### Before Starting

```bash
# Update local repository
git fetch upstream
git checkout main
git reset --hard upstream/main
```

### While Working

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make commits
git add changes
git commit -m "feat: add new feature"

# Keep up to date
git fetch upstream
git rebase upstream/main
```

### Before Submitting

```bash
# Final rebase
git rebase -i upstream/main  # Squash/organize commits if needed

# Run full test suite
pixi run test

# Run linting
pixi run black bactscout/ tests/
pixi run flake8 bactscout/ tests/

# Push to your fork
git push origin feature/my-feature
```

## Release Process

BactScout uses semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Releases are tagged and published to GitHub.

## Getting Help

### Resources

- **Documentation**: [https://bactscout.readthedocs.io/](./index.md)
- **Issues**: [GitHub Issues](https://github.com/nfareed/bactscout/issues)
- **Discussions**: GitHub Discussions (if enabled)

### Ask Questions

- Create an issue with question tag
- Comment on related issues
- Check documentation first

## Community

BactScout is an open-source project. We welcome:
- Bug reports
- Feature requests
- Pull requests
- Documentation improvements
- Testing and feedback
- Use cases and research

All contributions help make BactScout better!

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

Thank you for contributing to BactScout! 🎉
