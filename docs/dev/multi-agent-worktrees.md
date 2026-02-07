# Multi-Agent Workflow with Git Worktrees

This repo includes a lightweight helper (`./agentctl`) for running one orchestrator agent and multiple implementation subagents in parallel.

## Why this mode
- Each agent gets its own branch + checkout directory.
- No branch switching conflicts.
- Orchestrator can refine specs and merge finished subagent work safely.

## One-time setup
```bash
# from repo root
./agentctl init
./agentctl paths
```

Default worktree root is a sibling folder:
- `../planetarion-worktrees`

Override with:
```bash
export WORKTREE_ROOT=/absolute/path/to/worktrees
```

## Core commands
```bash
./agentctl list
./agentctl new orchestrator <slug> [base_branch]
./agentctl new worker <slug> [base_branch]
./agentctl spawn <task_id> <slug> [base_branch]
./agentctl rm <slug> [--delete-branch]
```

## Recommended daily flow

### 1) Orchestrator session
```bash
./agentctl new orchestrator planning main
```
Open: `../planetarion-worktrees/orchestrator-planning`

Use orchestrator for:
- Spec refinement
- Task splitting
- Review and merge decisions

### 2) Create task briefs
Task briefs live in:
- `.orchestrator/tasks/<task_id>.md`

Create from template:
```bash
cp .orchestrator/templates/task-brief.md .orchestrator/tasks/task-001.md
```

### 3) Spawn subagents from tasks
```bash
./agentctl spawn task-001 fleet-templates main
./agentctl spawn task-002 combat-cta main
./agentctl spawn task-003 quest-helper main
```

Each subagent gets:
- Branch: `agent/<slug>`
- Worktree: `../planetarion-worktrees/worker-<slug>`
- Seed task file: `.agent-task.md`

### 4) Run agents in parallel
- Start a Cursor/Codex session in each `worker-*` directory.
- Keep each agent scoped to its task brief.

### 5) Merge via orchestrator
From orchestrator worktree, merge/cherry-pick worker branches after review:
```bash
# example from orchestrator branch
git fetch --all
# then merge or cherry-pick as preferred
```

### 6) Cleanup finished workers
```bash
./agentctl rm fleet-templates --delete-branch
./agentctl rm combat-cta --delete-branch
```

## Human conventions (short)
- Branch names:
  - Orchestrator: `orchestrator/<slug>`
  - Subagent: `agent/<slug>`
- Keep commits small and task-focused.
- Require tests in every subagent branch.
- Orchestrator owns final integration test gate.

## Included templates
- `.orchestrator/templates/task-brief.md`
- `.orchestrator/templates/subagent-task.md`
- `.orchestrator/templates/orchestrator-session.md`
- `.orchestrator/templates/merge-checklist.md`

## Low-manual orchestration helpers

These helpers reduce manual status collection and merge gating.

### Files
- `.orchestrator/workers.json` (worker mapping + merge order)
- `.orchestrator/bin/status-write` (worker heartbeat/status writer)
- `.orchestrator/bin/status-poll` (orchestrator status collector)
- `.orchestrator/bin/merge-gate` (ordered merge readiness check)

### Worker update command
From a worker worktree:
```bash
/home/yves/repos/planetarion/.orchestrator/bin/status-write \
  <task_id> <worker_slug> <progress_0_100> <eta> "<summary>" [blocker] [commit_sha]
```

Environment-driven mode (no positional args):
```bash
export TASK_ID=task-202-fleet-rebalance
export WORKER_SLUG=fleet-rebalance
export PROGRESS=85
export ETA="25m"
export SUMMARY="Split endpoint done, transfer tests in progress"
export BLOCKER=""
export COMMIT_SHA="$(git rev-parse HEAD)"
/home/yves/repos/planetarion/.orchestrator/bin/status-write
```

Example:
```bash
/home/yves/repos/planetarion/.orchestrator/bin/status-write \
  task-202-fleet-rebalance fleet-rebalance 85 "25m" \
  "Split endpoint done, transfer tests in progress"
```

### Orchestrator control loop
From any repo/worktree:
```bash
/home/yves/repos/planetarion/.orchestrator/bin/status-poll
/home/yves/repos/planetarion/.orchestrator/bin/merge-gate
```

What `merge-gate` checks:
- strict merge order from `.orchestrator/workers.json`
- worker branch exists
- branch already merged or ready/hold
- readiness based on status file (`progress`, `blocker`, `commit_sha`, passing tests list)

When a branch is `READY`, `merge-gate` prints the exact next merge command.

## Shared Scratchpad Orchestration (Simple Mode)

You can run a lighter orchestration model with separate worktrees while all agents report into a shared scratchpad in the orchestrator repo.

### Goal
- Keep parallel implementation work in isolated worktrees.
- Keep status tracking in one shared place the orchestrator can read quickly.

### Recommended write model
Avoid concurrent edits to the same lines. Use one of these patterns:

1. Per-agent status files (recommended)
- Path pattern: `.orchestrator/status/<worker-slug>.md`
- Each agent owns only its own file.
- Orchestrator reads all files and synthesizes decisions.

2. Single append-only log file
- Path: `.orchestrator/status/scratchpad.log`
- Each agent appends one-line updates only.
- No edits/deletes; orchestrator uses latest line per worker.

3. Single table file with lock
- Path: `.orchestrator/status/scratchpad.md` or `.json`
- Agents must acquire a lock before writing (e.g. `flock`).
- Use when you need one canonical table view.

### Minimal table shape (if using one file)
- `task_id`
- `worker_slug`
- `branch`
- `progress` (0-100)
- `eta`
- `summary`
- `blocker`
- `last_commit`
- `last_update_utc`

### Practical recommendation for this repo
- Keep current `.orchestrator/bin/status-write` flow.
- Back it with per-agent files under `.orchestrator/status/` to avoid merge/write conflicts.
- Let orchestrator run `status-poll` + `merge-gate` to derive merge order and readiness.
