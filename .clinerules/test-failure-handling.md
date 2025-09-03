## Brief overview
This rule defines intelligent test failure handling to improve development workflow efficiency. When tests fail consistently, the system automatically switches to PLAN mode to analyze and resolve underlying issues.

## Failure Tracking
- Track consecutive test failures by test type and error pattern
- Maintain failure history in `.test-failures.log` file
- Reset failure count when test passes or error pattern changes

## Plan Mode Triggers
- **5 consecutive failures** of the same test type with identical error pattern
- **3 consecutive failures** across different test types with related errors
- **Immediate trigger** for critical errors (import failures, environment issues)

## Failure Analysis
- Log error patterns, timestamps, and test context
- Identify common failure categories:
  - Import/path issues
  - Environment/configuration problems
  - Test data/setup failures
  - Code logic errors

## Recovery Actions
- Auto PLAN mode activation with failure analysis
- Suggest specific debugging commands based on failure type
- Provide context about recent code changes that may have caused failures

## Development Workflow Integration
- Seamless transition between ACT and PLAN modes
- Preserve test context when switching modes
- Resume testing from last failure point after fixes

## Logging and Reporting
- Maintain detailed failure logs for pattern analysis
- Generate failure reports for debugging assistance
- Track resolution time and effectiveness of fixes
