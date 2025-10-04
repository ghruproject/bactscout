# Test Coverage Report

This project uses `coverage.py` and `pytest-cov` for test coverage analysis.

## Running Coverage

```bash
# Run tests with coverage
pixi run test-cov

# Generate HTML coverage report
pixi run cov-report

# View coverage report
open htmlcov/index.html
```

## Current Coverage

**Total Coverage: 67%**

### Module Breakdown:
- `bactscout/__init__.py`: 100%
- `bactscout/__version__.py`: 100% 
- `bactscout/util.py`: 100%
- `bactscout/main.py`: 82%
- `bactscout/software/run_sylph.py`: 81%
- `bactscout/summary.py`: 76%
- `bactscout/thread.py`: 69%
- `bactscout/preflight.py`: 65%
- `bactscout/software/run_fastp.py`: 58%
- `bactscout/software/run_stringmlst.py`: 15%

## Improving Coverage

Areas needing more test coverage:
- StringMLST module (15% - needs integration tests)
- Fastp module (58% - needs error handling tests)
- Preflight checks (65% - needs database/software validation tests)

The low coverage in some modules is expected as they involve:
- External software dependencies
- File system operations
- Network requests
- Error conditions that are hard to reproduce in tests

## CI/CD Integration

Coverage is automatically measured in GitHub Actions and reported to Codecov.