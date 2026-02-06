"""Central research definitions used by both routes and tick processing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchDef:
    key: str
    branch: str
    name: str
    base_cost: int
    max_level: int | None = None
    description: str = ""
    effect_hint: str = ""


RESEARCH_DEFS: list[ResearchDef] = [
    # Expansion
    ResearchDef(
        key="colonization_tech",
        branch="Expansion",
        name="Colonization Tech",
        base_cost=100,
        max_level=10,
        description="Unlocks colonization of higher-difficulty targets.",
        effect_hint="Allows colonizing planets up to difficulty = level.",
    ),
    ResearchDef(
        key="astrophysics",
        branch="Expansion",
        name="Astrophysics",
        base_cost=150,
        max_level=15,
        description="Improves travel time and expansion capacity.",
        effect_hint="Reduces travel time; increases colony cap.",
    ),
    ResearchDef(
        key="interstellar_communication",
        branch="Expansion",
        name="Interstellar Communication",
        base_cost=200,
        max_level=12,
        description="Improves galaxy visibility and coordination.",
        effect_hint="Increases nearby systems range.",
    ),
    ResearchDef(
        key="espionage_tech",
        branch="Expansion",
        name="Espionage Tech",
        base_cost=140,
        max_level=15,
        description="Improves scouting/espionage effectiveness.",
        effect_hint="Better intel and probe outcomes (future).",
    ),
    # Economy
    ResearchDef(
        key="energy_tech",
        branch="Economy",
        name="Energy Tech",
        base_cost=120,
        max_level=20,
        description="Improves energy efficiency.",
        effect_hint="Higher effective production via energy ratio (future).",
    ),
    ResearchDef(
        key="computer_tech",
        branch="Economy",
        name="Computer Tech",
        base_cost=120,
        max_level=20,
        description="Improves operational efficiency.",
        effect_hint="Supports fleet templates / coordination (future).",
    ),
    ResearchDef(
        key="recycler_efficiency",
        branch="Economy",
        name="Recycler Efficiency",
        base_cost=130,
        max_level=20,
        description="Improves recycler yield/capacity.",
        effect_hint="+% recycler capacity (future).",
    ),
    # Combat
    ResearchDef(
        key="weapons_tech",
        branch="Combat",
        name="Weapons Tech",
        base_cost=160,
        max_level=20,
        description="Improves weapon damage.",
        effect_hint="+% damage (future).",
    ),
    ResearchDef(
        key="shielding_tech",
        branch="Combat",
        name="Shielding Tech",
        base_cost=160,
        max_level=20,
        description="Improves shield strength.",
        effect_hint="+% shields (future).",
    ),
    ResearchDef(
        key="armour_tech",
        branch="Combat",
        name="Armor Tech",
        base_cost=160,
        max_level=20,
        description="Improves hull/armor.",
        effect_hint="+% HP (future).",
    ),
]


RESEARCH_DEF_BY_KEY = {d.key: d for d in RESEARCH_DEFS}
RESEARCH_KEYS = tuple(d.key for d in RESEARCH_DEFS)
RESEARCH_BRANCHES = tuple(sorted({d.branch for d in RESEARCH_DEFS}))

