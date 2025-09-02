# Workflow Rules

## Run Tests Before Commit
- **Value:** `true`

## Test Command
- **Value:** `pytest gameserver/tests/unit tests/integration && npx playwright test gameserver/tests/e2e`

## Commit Only on Success
- **Value:** `true`

## Push to Remote
- **Value:** `true`

## Branch
- **Value:** `main`

## Summary
### Enabled
- **Value:** `true`

### File
- **Value:** `CLINE_SUMMARY.md`

### Include
- `task_name`
- `files_changed`
- `test_results`
- `timestamp`

## Notifications
### On Failure
- **Value:** `print`

### On Success
- **Value:** `append_summary`

## Paths
### Root
- **Value:** `planetarion`

### Tasks Folder
- **Value:** `.cline/tasks`

### Project Folder
- **Value:** `gameserver`
