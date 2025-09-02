# Workflow Rules

## Memory Bank Updates Before Commit
- **Value:** `true`
- **Instruction:** Always keep `activeContext.md` and `progress.md` up to date before committing code.

## Run Tests Before Commit
- **Value:** `true`

## Test Command
- **Value:** `./run-tests.sh all`

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
- **Value:** `.clinerules/tasks`

### Project Folder
- **Value:** `game-server`
