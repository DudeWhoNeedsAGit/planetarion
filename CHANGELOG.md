# Changelog

All notable gameplay-impacting changes are documented in this file.

## 2026-02-07

### Added
- Pirate simulation expansion loop (config-gated):
  - Pirate factions can launch colonization fleets toward neutral planets.
  - Expansion cadence is interval-based and emits dedicated tick-log events.
- Anti-snowball caps for pirate expansion:
  - Per-faction planet cap.
  - Per-Z-slice cap.
  - Global pirate planet cap.
  - Home-planet buffer distance that blocks pirate colonization near player home worlds.
- Pirate faction utilities:
  - Central helper for identifying pirate NPC users via configured faction usernames.
  - Unit coverage for faction identification behavior.

### Changed
- Pirate handling generalized from a single hardcoded `pirates` user to configurable pirate faction usernames across core systems:
  - Fleet attack protection checks.
  - Fleet arrival pirate attacker behavior.
  - Tick and idle-catchup NPC filtering.
  - Commander XP exclusion for pirate NPC users.
  - Combat engine pirate ownership/name handling.
  - Pirate AI status and runtime filtering.
- Resource and key value displays switched to compact notation in core frontend gameplay screens (`T`, `M`, `B`, `Tr`, `Qa`) to improve readability at large scales.

### Fixed
- Prevented gameplay logic from relying on strict single-username pirate assumptions, reducing edge-case regressions when introducing multiple pirate factions.
- Added targeted tests for pirate expansion behavior and cap enforcement, plus regression coverage for pirate combat/XP interactions.
