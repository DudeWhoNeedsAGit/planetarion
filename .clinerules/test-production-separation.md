## Brief overview
This rule ensures production code remains unchanged when fixing test execution issues. Test problems should be resolved through test configuration, environment setup, or test-specific workarounds, never by modifying working production functionality.

## Test Execution Issues
- **File path problems**: Fix through PYTHONPATH configuration, test directory structure, or pytest configuration
- **Import resolution**: Use test-specific imports, virtual environments, or module path adjustments
- **Environment differences**: Configure test environment to match production expectations

## Production Code Protection
- **Never modify working production imports** for test convenience
- **Preserve relative imports** used in production (`from .module import X`)
- **Maintain production package structure** and module relationships
- **Keep production logic intact** regardless of test execution challenges

## Test Configuration Solutions
- **PYTHONPATH manipulation**: Set correct module paths for test execution
- **Virtual environment setup**: Isolate test dependencies from production
- **Test-specific entry points**: Create test wrappers that handle import differences
- **Pytest configuration**: Use conftest.py, pytest.ini, or setup.cfg for test-specific settings

## When to Modify Production Code
- **Only for legitimate production issues** (bugs, performance, functionality)
- **Never for test execution convenience**
- **Always verify production still works** after any changes
- **Test both production and test environments** after modifications

## Development Workflow
- **Identify root cause**: Is it a test configuration issue or production code issue?
- **Test configuration first**: Try PYTHONPATH, environment, and pytest settings
- **Production changes last**: Only when all test configuration options are exhausted
- **Document workarounds**: Note test-specific configurations for future reference
