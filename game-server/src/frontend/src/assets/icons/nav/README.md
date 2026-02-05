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

The script creates `_backup_pre_rembg_<timestamp>/` next to the images.
