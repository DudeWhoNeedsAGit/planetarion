# Commander Portrait Assets

These images are source assets for the commander portrait + level-dependent frames.

## Canonical filenames

- `commander_portrait_base.png`
- `female_commander.png` (source option)
- `male_commander.png` (source option)
- `commander_frame_tier1_l01-05.png`
- `commander_frame_tier2_l06-10.png`
- `commander_frame_tier3_l11-15.png`
- `commander_frame_tier4_l16-20.png`
- `commander_frame_tier5_l21-25.png`

## Background removal / alpha channel (rembg)

If an image was generated with a solid background, use `rembg` to remove it and write proper transparency.

From repo root:

- Install (once): `game-server/venv/bin/pip install "rembg[cpu]"`
- Process this folder (backs up, overwrites in-place): `game-server/venv/bin/python game-server/scripts/rembg_batch.py docs/assets/images/portrait`

The batch script creates a timestamped `_backup_pre_rembg_<timestamp>/` folder next to the images.
