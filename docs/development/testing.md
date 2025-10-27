# Testing Guide

This guide explains BactScout's testing infrastructure and how to write tests.

## Test Suite Overview

BactScout has **98 comprehensive tests** organized into 5 test modules:

| Module | Tests | Coverage |
|--------|-------|----------|
| `test_fastp.py` | 56 | fastp data extraction |
| `test_stringmlst.py` | 13 | MLST typing |
| `test_main.py` | 4 | Pipeline logic |
| `test_file_pairs.py` | 10 | FASTQ pair discovery |
| `test_bactscout_cli.py` | 16 | CLI interface |
| **Total** | **98** | **100% passing** |

## Running Tests

### Run All Tests

```bash
pixi run test
```

Output: Summary of all test results and coverage.

### Run Specific Module

```bash
pixi run pytest tests/test_fastp.py -v
pixi run pytest tests/test_stringmlst.py -v
pixi run pytest tests/test_bactscout_cli.py -v
```

### Run Single Test

```bash
pixi run pytest tests/test_fastp.py::test_extract_coverage -v
```

### Run with Coverage Report

```bash
pixi run pytest tests/ --cov=bactscout --cov-report=html
```

Coverage report saved to `htmlcov/index.html`

### Run in Watch Mode

```bash
pixi run pytest-watch
```

Tests run automatically when files change.

## Test Organization

### `test_fastp.py` - Fastp Data Extraction (56 tests)

Tests fastp JSON parsing and metric extraction.

**Key test categories**:
- Valid JSON parsing
- Metric calculations (coverage, Q30%, read length)
- Edge cases (empty files, corrupted JSON)
- Error handling

**Example test**:
```python
def test_extract_coverage_from_fastp_json():
    """Test coverage calculation from fastp JSON."""
    json_data = {
        "summary": {
            "after_filtering": {
                "total_bases": 150_000_000
            }
        }
    }
    coverage = extract_coverage(json_data, ref_size=5)  # 5 Mb
    assert coverage == pytest.approx(30.0)
```

**Run**:
```bash
pixi run pytest tests/test_fastp.py -v
```

### `test_stringmlst.py` - MLST Typing (13 tests)

Tests MLST result parsing and ST determination.

**Key test categories**:
- Valid MLST JSON parsing
- Allele extraction
- Sequence type assignment
- Status determination (complete, partial, etc.)

**Example test**:
```python
def test_extract_mlst_st():
    """Test ST extraction from MLST results."""
    json_data = {
        "st": "ST-10",
        "species": "Escherichia coli",
        "status": "complete"
    }
    st = extract_st(json_data)
    assert st == "ST-10"
```

**Run**:
```bash
pixi run pytest tests/test_stringmlst.py -v
```

### `test_main.py` - Pipeline Logic (4 tests)

Tests core pipeline functions.

**Key test categories**:
- Configuration loading
- Results aggregation
- CSV generation

**Example test**:
```python
def test_aggregate_results():
    """Test per-sample result aggregation."""
    results = [
        {"sample_id": "s1", "coverage": 50},
        {"sample_id": "s2", "coverage": 60}
    ]
    agg = aggregate_results(results)
    assert len(agg) == 2
    assert agg[0]["sample_id"] == "s1"
```

**Run**:
```bash
pixi run pytest tests/test_main.py -v
```

### `test_file_pairs.py` - FASTQ Discovery (10 tests)

Tests FASTQ file pair detection and naming.

**Key test categories**:
- Pair matching (_R1/_R2, _1/_2)
- File filtering
- Error handling for unpaired files

**Example test**:
```python
def test_locate_fastq_pairs(tmp_path):
    """Test FASTQ pair discovery."""
    # Create test files
    (tmp_path / "sample_R1.fastq.gz").touch()
    (tmp_path / "sample_R2.fastq.gz").touch()
    
    pairs = locate_read_file_pairs(tmp_path)
    assert len(pairs) == 1
    assert pairs[0][0].name == "sample_R1.fastq.gz"
```

**Run**:
```bash
pixi run pytest tests/test_file_pairs.py -v
```

### `test_bactscout_cli.py` - CLI Interface (16 tests)

Tests command-line interface and argument parsing.

**Key test categories**:
- Command existence
- Help text display
- Argument validation
- Short flag support
- Error handling

**Example test**:
```python
def test_qc_command_exists():
    """Test that 'qc' command exists."""
    result = subprocess.run(
        ["pixi", "run", "bactscout", "qc", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "quality control" in result.stdout.lower()
```

**Run**:
```bash
pixi run pytest tests/test_bactscout_cli.py -v
```

## Writing New Tests

### Test File Structure

```python
import pytest
from bactscout.module import function_to_test

class TestFunctionName:
    """Tests for function_to_test."""
    
    def test_basic_functionality(self):
        """Test basic operation."""
        result = function_to_test(input_data)
        assert result == expected_output
    
    def test_edge_case(self):
        """Test edge case."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
    
    @pytest.mark.parametrize("input,expected", [
        ("case1", "result1"),
        ("case2", "result2"),
    ])
    def test_multiple_cases(self, input, expected):
        """Test multiple input cases."""
        result = function_to_test(input)
        assert result == expected
```

### Common Pytest Patterns

**Test fixtures**:
```python
@pytest.fixture
def sample_json():
    """Fixture providing sample data."""
    return {
        "summary": {
            "after_filtering": {"total_bases": 150_000_000}
        }
    }

def test_with_fixture(sample_json):
    """Test using fixture."""
    result = process(sample_json)
    assert result == expected
```

**Temporary files**:
```python
def test_file_operations(tmp_path):
    """Test with temporary directory."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("data")
    
    result = read_file(test_file)
    assert result == "data"
```

**Mocking**:
```python
from unittest.mock import patch

def test_external_call():
    """Test with mocked external function."""
    with patch('bactscout.module.external_func') as mock:
        mock.return_value = "mocked_result"
        
        result = function_that_calls_external()
        assert result == "mocked_result"
        mock.assert_called_once()
```

**Parametrized tests**:
```python
@pytest.mark.parametrize("coverage,q30,passes", [
    (50, 90, True),    # Good
    (20, 90, False),   # Low coverage
    (50, 70, False),   # Low Q30
])
def test_quality_thresholds(coverage, q30, passes):
    """Test QC threshold determination."""
    result = check_quality(coverage, q30)
    assert result == passes
```

**Expected exceptions**:
```python
def test_invalid_input():
    """Test error handling."""
    with pytest.raises(ValueError, match="Invalid input"):
        process_data(invalid_data)
```

## Adding New Tests

### 1. Identify What to Test

When adding a new function or fixing a bug, write tests for:
- **Happy path**: Normal operation with valid input
- **Edge cases**: Boundary conditions (empty, minimum, maximum)
- **Error cases**: Invalid input, expected exceptions
- **Integration**: How function works with others

### 2. Create Test File or Add to Existing

```bash
# New feature
vi tests/test_new_feature.py

# Or add to existing file
vi tests/test_existing.py
```

### 3. Write Tests

```python
# tests/test_new_feature.py
import pytest
from bactscout.new_module import new_function

def test_new_function_basic():
    """Test basic functionality."""
    result = new_function("input")
    assert result == "expected"

def test_new_function_edge_case():
    """Test edge case."""
    with pytest.raises(ValueError):
        new_function(invalid_input)
```

### 4. Run and Verify

```bash
pixi run pytest tests/test_new_feature.py -v
```

### 5. Check Coverage

```bash
pixi run pytest tests/test_new_feature.py --cov=bactscout --cov-report=term-missing
```

Aim for 80%+ coverage of new code.

## Continuous Integration

### GitHub Actions

Tests run automatically on every commit:

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: ./.github/actions/setup-pixi
      - run: pixi run test
      - run: pixi run pytest --cov-report=xml
      - uses: codecov/codecov-action@v3
```

**Checks**:
- All 98 tests pass ✓
- Code coverage maintained
- No regressions

### Local CI Simulation

```bash
# Run full CI locally
pixi run test
pixi run pytest --cov=bactscout --cov-report=html
pixi run lint
```

## Best Practices

### DO

✅ **Write tests as you code**
- Test-driven development (TDD)
- Write test before implementation
- Catch bugs early

✅ **Test behavior, not implementation**
- Test what function does, not how
- Tests survive refactoring
- Focus on public interface

✅ **Use descriptive test names**
- `test_extract_coverage_from_valid_json()` ✓
- `test_coverage()` ✗

✅ **Test edge cases**
- Empty input
- Very large input
- Invalid input
- Boundary conditions

✅ **Keep tests focused**
- One assertion per test (ideally)
- Or tightly related assertions
- Easy to understand what failed

### DON'T

❌ **Don't test implementation details**
- Don't test private functions
- Don't care about internal structure
- Test public API only

❌ **Don't create test interdependencies**
- Tests must be order-independent
- Each test should stand alone
- Use fixtures for shared setup

❌ **Don't hardcode test data**
- Use fixtures or generate data
- Make tests maintainable
- Use parametrization for variations

❌ **Don't skip or xfail tests**
- If test fails, fix it or delete it
- Don't hide failing tests
- Address technical debt

## Test Utilities

### Available Fixtures

```python
# Use in tests with decorator or parameter
@pytest.fixture
def tmp_path():
    """Temporary directory."""
    # Unique temp dir provided by pytest

@pytest.fixture
def monkeypatch():
    """Monkey patch (mocking)."""
    # Modify attributes/environment

@pytest.fixture
def capsys():
    """Capture stdout/stderr."""
    # Capture printed output
```

### Common Assertions

```python
# Equality
assert result == expected

# Boolean
assert result is True
assert result is None

# Exceptions
with pytest.raises(ValueError):
    problematic_code()

# Approximate equality
assert result == pytest.approx(expected, rel=1e-5)

# Membership
assert item in collection

# Patterns (regex)
with pytest.raises(ValueError, match="pattern"):
    code()
```

## Debugging Tests

### Verbose Output

```bash
pixi run pytest tests/test_fastp.py -v -s
```

- `-v`: Verbose (show test names)
- `-s`: Show stdout (print statements)

### Debug with PDB

```python
def test_something():
    result = some_function()
    import pdb; pdb.set_trace()  # Debugger stops here
    assert result == expected
```

```bash
pixi run pytest tests/test_something.py -v -s
# Debugger will launch at breakpoint
```

### Show Slowest Tests

```bash
pixi run pytest tests/ -v --durations=10
```

### Run Only Failed Tests

```bash
pixi run pytest tests/ --lf
```

### Stop on First Failure

```bash
pixi run pytest tests/ -x
```

## Troubleshooting Tests

### "Test passes locally but fails in CI"

Common causes:
- Platform difference (Linux vs macOS)
- Environment difference (package version)
- File path issues (Windows vs Unix)
- Timing issues (temporary files)

Solutions:
- Check CI logs carefully
- Use absolute paths
- Handle platform differences
- Don't rely on system state

### "Fixture not found"

Solution:
```python
# Fixture must be in:
# 1. Same file
# 2. conftest.py (in tests/ directory)
# 3. Pytest built-in

# To share fixtures, create conftest.py
# tests/conftest.py
@pytest.fixture
def shared_data():
    return {...}
```

### "Test is non-deterministic" (flaky)

Common causes:
- Timing dependencies
- File system issues
- Network calls
- Randomization

Solutions:
- Add explicit waits
- Use mocks for external services
- Seed random generators
- Run test multiple times locally

## Performance Testing

### Profile Test Suite

```bash
pixi run pytest tests/ --profile
```

Shows which tests are slowest.

### Profile Individual Test

```bash
python -m pytest tests/test_fastp.py::test_specific -v --profile
```

## Test Data

### Sample Data Location

```
test_data/          # Real test FASTQ files
sample_data/        # Alternative test samples
tests/fixtures/     # Mock data (if created)
```

### Using Test Data

```python
def test_with_real_data():
    """Test using real FASTQ files."""
    r1 = Path("test_data/Sample_001_R1.fastq.gz")
    r2 = Path("test_data/Sample_001_R2.fastq.gz")
    
    result = process(r1, r2)
    assert result is not None
```

## See Also

- [Architecture Guide](./architecture.md) - System design
- [Contributing Guide](../contributing.md) - Contributing code
- [pytest documentation](https://docs.pytest.org/) - Official docs
