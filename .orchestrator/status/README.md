# Worker Status Contract

Each worker worktree writes a local `.agent-status.json` file at its repo root.

## Minimal required fields
- `task_id`
- `worker_slug`
- `progress` (0-100)
- `summary`
- `blocker` (empty string when clear)
- `eta`
- `commit_sha` (required for merge-ready state)
- `last_update` (UTC ISO8601)

## Optional but recommended fields
- `files_touched`: array of relative paths
- `tests`: array of objects `{ "command": "...", "result": "pass|fail" }`

## Quick write/update
From a worker worktree:

```bash
/home/yves/repos/planetarion/.orchestrator/bin/status-write \
  task-204-scenario-packs scenario-packs 70 "40m" \
  "Named endpoints done; finishing deterministic tests"
```

Environment-variable mode:

```bash
export TASK_ID=task-204-scenario-packs
export WORKER_SLUG=scenario-packs
export PROGRESS=70
export ETA="40m"
export SUMMARY="Named endpoints done; finishing deterministic tests"
export BLOCKER=""
export COMMIT_SHA=""
/home/yves/repos/planetarion/.orchestrator/bin/status-write
```

After commit:

```bash
/home/yves/repos/planetarion/.orchestrator/bin/status-write \
  task-204-scenario-packs scenario-packs 100 "0m" \
  "Task complete" "" "$(git rev-parse HEAD)"
```

If you need rich test/file metadata, edit `.agent-status.json` directly using
`.orchestrator/templates/agent-status.example.json` as reference.
