# .clinerules/tasks.md — Structural refactor tasks for **Planetarion**

> Purpose: a focused, **structure-only** refactor (no new tech, no library changes).
> Output: a ready-to-copy YAML task block (for `.clinerules/tasks.yml`) plus concise technical rationale, git commands to perform moves while preserving history, validation and rollback steps.

---

## Summary

This document encodes the structural refactor plan you asked for. It is *explicitly limited* to filesystem reorganization and documentation updates — **no code changes, no dependency additions, no runtime behavior changes**. The repo already contains separate Docker contexts for backend and frontend; this plan preserves those contexts and only reorganizes paths so the project layout is clearer and easier to maintain.

**How to use**

* Copy the YAML block below into `.clinerules/tasks.yml` if you want Cline to run the tasks.
* Or follow the `git mv` commands listed under each task to perform the moves manually (recommended for preserving history and review control).

---

## Rationale (technical, concise)

| Phase                  | Goal                                                   | Why (concise)                                                                                                                                                                                                                                   |
| ---------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `restructure-root`     | Create clear root boundaries (`services/`, `infra/`)   | Separates runtime services from infra; removes ambiguity about which directory is authoritative. Enables clearer CI/CD and on-ramp for new contributors. Preserves existing build/runtime semantics by moving files rather than modifying them. |
| `restructure-services` | Canonical `services/backend/` and `services/frontend/` | Standard multi-service monorepo layout: easier to target builds, tests, and reviewer focus. Keeps Docker contexts intact so no tech changes needed.                                                                                             |
| `cleanup-legacy`       | Remove duplicate/empty legacy paths                    | Eliminates confusion and stale paths; avoids accidental edits to obsolete locations.                                                                                                                                                            |
| `update-readme-paths`  | Fix developer UX docs                                  | README must point to new paths so `make`/`docker-compose` commands continue to work for devs.                                                                                                                                                   |
| `final-check`          | Validate smoke checks and rollback plan                | Ensure nothing is broken and that the changes are reversible.                                                                                                                                                                                   |

Key constraints respected:

* **No runtime changes**: Dockerfiles remain where they are; compose files are moved into `infra/` but not changed in content.
* **History preservation**: all moves are recommended via `git mv` so file history is preserved.
* **Incremental and reversible**: each task is small, testable, and can be reverted by resetting the branch.

---

## Recommended git workflow (short)

```bash
git checkout -b refactor/structure
# perform individual git mv operations per task
git add -A
git commit -m "refactor: move files — restructure repo layout (phase X)"
# open PR with small focused commits per phase
```

**Rollback**: if something goes wrong, `git reset --hard origin/main` on the branch or checkout the previous commit.

---

## Validation checks (per task)

* After each task/commit run:

  * `git status` to confirm moved files only
  * `ls services/backend` and `ls services/frontend` to confirm content
  * `grep -R "game-server/frontend" -n` (or equivalent) to ensure no remaining hardcoded paths in docs
  * Run `docker compose -f infra/docker-compose.dev.yml up --build` (dev machine) to confirm Docker contexts still work (no content change to compose files)

---

## .clinerules/tasks.yml (copy this block to `.clinerules/tasks.yml`)

```yaml
version: 1

tasks:
  - id: restructure-root
    title: "Restructure root & consolidate directories"
    description: |
      - Create canonical top-level folders: `services/` and `infra/`.
      - Move `game-server/` → `services/backend/` (preserve backend docker context).
      - Move `game-server/frontend/` → `services/frontend/` (preserve frontend docker context).
      - Move top-level `docker-compose*.yml`, `deploy-*` scripts, and any `docker/` dirs into `infra/`.
      - Do NOT change contents of Dockerfiles or compose files — only relocate them.
    operations:
      - op: git-mv
        src: game-server
        dst: services/backend
      - op: git-mv
        src: game-server/frontend
        dst: services/frontend
      - op: mkdir
        path: infra
      - op: git-mv
        src: "docker-compose.yml"
        dst: infra/docker-compose.yml
      - op: git-mv
        src: "docker-compose.dev.yml"
        dst: infra/docker-compose.dev.yml
      - op: git-mv
        src: "deploy-to-qnap.sh"
        dst: infra/deploy-to-qnap.sh

  - id: restructure-services
    title: "Populate services/ and infra/ with remaining artifacts"
    description: |
      - Ensure all service-level files are under `services/backend/` and `services/frontend/`.
      - Move any remaining infra artifacts (scripts, .env templates, compose variants) under `infra/`.
      - Update only docs/README paths — do NOT touch runtime config inside compose files.
    operations:
      - op: git-mv
        src: game-server/docker-compose.qnap.yml
        dst: infra/docker-compose.qnap.yml
      - op: git-mv
        src: game-server/deploy-*.sh
        dst: infra/
      - op: git-mv
        src: game-server/docs
        dst: services/backend/docs

  - id: cleanup-legacy
    title: "Remove legacy duplicate directories"
    description: |
      - Delete now-empty legacy paths such as any stale `game-server/frontend` leftover directory.
      - Keep `.gitignore`, `.clinerules/`, `memory-bank/` at root.
    operations:
      - op: remove-dir
        path: game-server

  - id: update-readme-paths
    title: "Update README paths to reflect new layout"
    description: |
      - Replace examples and developer commands in README.md to point to `services/backend` and `services/frontend`.
      - Do not change tutorial steps or command semantics — only adjust paths.
    operations:
      - op: replace-in-file
        path: README.md
        pattern: "game-server/frontend"
        replacement: "services/frontend"
      - op: replace-in-file
        path: README.md
        pattern: "game-server"
        replacement: "services/backend"

  - id: final-check
    title: "Final smoke and sanity checks"
    description: |
      - Confirm all moves preserved history via `git log --follow` on moved files.
      - Run quick directory checks and dev docker-compose up to ensure contexts remain valid.
      - Document any manual steps required for CI (if pipeline references moved paths).
    operations:
      - op: run
        cmd: |
          git --no-pager status --porcelain
          ls -la services
          grep -R "game-server" -n || true

```

---

## Task-level notes (short, technical)

* **`git-mv` use is mandatory**: preserves file history and simplifies PR review. Avoid manual copy/delete unless absolutely necessary.
* **No file content changes**: The operations only move files and replace README path strings where needed. This ensures runtime equivalence.
* **CI tokens/paths**: If your CI references `game-server/` paths, update CI config after `update-readme-paths` stage; do this in a dedicated PR to keep rollout safe.
* **Docker contexts**: Because the Dockerfiles remain inside `services/backend` and `services/frontend`, builds should continue to work. If compose uses relative paths, moving compose into `infra/` keeps files colocated but you may need to adjust `context` fields if they used `../` references — check these manually post-move.

---

## Quick manual `git mv` cheat-sheet (example commands)

```bash
# from repo root
git checkout -b refactor/structure
# move backend whole folder
git mv game-server services/backend
# move frontend (if it exists separately)
git mv services/backend/frontend services/frontend
# create infra and move compose files
mkdir infra
git mv docker-compose.yml infra/docker-compose.yml || true
git mv docker-compose.qnap.yml infra/docker-compose.qnap.yml || true
# commit per-phase
git add -A
git commit -m "refactor(structure): move services and infra — phase 0"
```

> Note: the `|| true` guards are for idempotence in scripted runs where a particular file might not exist.
