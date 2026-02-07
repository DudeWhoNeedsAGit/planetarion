Place navigation icons here as SVGs or PNGs to replace emoji in the top navigation.

Naming convention (lowercase, `.svg` preferred, `.png` supported):
- `overview.svg`
- `planets.svg`
- `galaxy.svg`
- `fleets.svg`
- `combat.svg`
- `wheel.svg`
- `shipyard.svg`
- `research.svg`
- `alliance.svg`
- `messages.svg`

The UI auto-loads known icon ids from this folder via `require.context` and falls back to emoji if an icon is missing.

## Making PNGs transparent (rembg)

If your generated PNGs have a solid background, `rembg` can remove it and add a proper alpha channel.

From repo root:
- Install (once): `game-server/venv/bin/pip install "rembg[cpu]"`
- Process this folder (backs up, overwrites in-place): `game-server/venv/bin/python game-server/scripts/rembg_batch.py game-server/src/frontend/src/assets/icons/nav`

Notes:
- The script creates `_backup_pre_rembg_<timestamp>/` next to the images (unless `--out-dir` or `--no-backup` is used).
- Use `--dry-run` to see what would change without modifying anything.
- Use `--recursive` to process subfolders, and `--pattern` for non-PNG inputs.

Examples (any folder):
- In-place + backup: `game-server/venv/bin/python game-server/scripts/rembg_batch.py path/to/folder`
- Non-destructive output: `game-server/venv/bin/python game-server/scripts/rembg_batch.py path/to/folder --out-dir path/to/output`
- Recurse: `game-server/venv/bin/python game-server/scripts/rembg_batch.py path/to/folder --recursive`

## Background music asset

For the in-game background track, the canonical file lives at:
- `game-server/src/frontend/public/audio/Planetarion.mp3`
