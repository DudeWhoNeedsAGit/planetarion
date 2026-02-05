# Dead code tracer (Python)

This repo includes a small utility that combines:

- **Dynamic reachability** via `coverage.py` (what lines were executed)
- **Static unused-symbol hints** via `vulture` (what *looks* unused)

The overlap (“vulture says unused” **and** “coverage never executed”) is usually a good shortlist for actual dead code.

## Install (per-venv)

In the Python environment you use to run tests/server:

```bash
python -m pip install coverage vulture
```

## Usage

From the repo root:

```bash
./cline-scripts/dead_code_tracer.py --project-root game-server --python game-server/venv/bin/python --source src
```

Run tests under coverage (default `python -m pytest`):

```bash
./cline-scripts/dead_code_tracer.py \
  --project-root game-server \
  --python game-server/venv/bin/python \
  --source src \
  --tests "python -m pytest tests/unit"
```

Add a short manual session (start backend under coverage; stop with Ctrl-C):

```bash
./cline-scripts/dead_code_tracer.py \
  --project-root game-server \
  --python game-server/venv/bin/python \
  --source src \
  --tests "python -m pytest tests/unit" \
  --run "python -m src"
```

Add env vars (repeatable):

```bash
./cline-scripts/dead_code_tracer.py \
  --project-root game-server \
  --python game-server/venv/bin/python \
  --source src \
  --env "DATABASE_URL=sqlite:////tmp/planetarion_deadcode.db" \
  --tests "python -m pytest tests/integration"
```

## Output

Artifacts go to `<project-root>/.deadcode/<timestamp>/`:

- `deadcode_report.md` – human-friendly summary
- `coverage.json` – structured coverage data (if coverage ran)
- `vulture.txt` – raw vulture output (if vulture ran)

## Notes / limitations

- If you pass a non-Python test command (example: `make unit`), the script can’t reliably inject `coverage run` into the inner `python` calls; it will run the command but won’t produce useful coverage.
- Multi-process coverage (backend + workers) needs extra configuration (`coverage process_startup`). This script currently targets **single-process** runs (pytest + a single backend process).

