## Brief overview
Guidelines for executing Docker commands and test scripts in this project, ensuring proper permissions and workflow integration.

## Docker command execution
- Execute Docker commands with sudo to ensure proper permissions and avoid permission errors
- Use sudo for all docker and docker-compose commands in the project environment

## Test script execution
- Use the run-tests.sh script for comprehensive testing instead of direct test commands
- Run tests before committing code to maintain quality standards
- The run-tests.sh script handles Docker-based testing for both backend and frontend components

## Workflow integration
- Integrate Docker command execution into the development workflow
- Ensure sudo is used consistently for all container management operations
- Use the project's test runner script for automated testing procedures

## Cleanup
- Watch for orphanded docker containers from old test executions and remove them

## Verbosity
- When executing the run-test.sh use -verbose for checking test failure reasons