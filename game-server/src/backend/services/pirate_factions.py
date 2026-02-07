from __future__ import annotations

from collections.abc import Iterable

from flask import current_app, has_app_context

DEFAULT_PIRATE_FACTION_USERNAMES: tuple[str, ...] = ("pirates", "pirates_red", "pirates_black")


def configured_pirate_usernames(config: object | None = None) -> set[str]:
    cfg = config
    if cfg is None and has_app_context():
        cfg = current_app.config

    raw = None
    if cfg is not None:
        raw = getattr(cfg, "get", lambda *_: None)("PIRATE_FACTION_USERNAMES")

    parsed = {
        str(part or "").strip().lower()
        for part in str(raw or "").split(",")
        if str(part or "").strip()
    }

    if not parsed:
        parsed = {name.lower() for name in DEFAULT_PIRATE_FACTION_USERNAMES}

    # Preserve backward compatibility with existing data/tests.
    parsed.add("pirates")
    return parsed


def is_pirate_username(username: str | None, config: object | None = None) -> bool:
    if not username:
        return False
    return str(username).strip().lower() in configured_pirate_usernames(config=config)


def is_pirate_user(user: object | None, config: object | None = None) -> bool:
    if not user:
        return False
    return is_pirate_username(getattr(user, "username", None), config=config)


def filter_pirate_users(users: Iterable[object], config: object | None = None) -> list[object]:
    return [u for u in users if is_pirate_user(u, config=config)]


def select_primary_pirate_user(users: Iterable[object], config: object | None = None) -> object | None:
    pirate_users = filter_pirate_users(users, config=config)
    if not pirate_users:
        return None

    by_name = {str(getattr(u, "username", "")).strip().lower(): u for u in pirate_users}
    if "pirates" in by_name:
        return by_name["pirates"]

    return sorted(pirate_users, key=lambda u: int(getattr(u, "id", 10**12) or 10**12))[0]
