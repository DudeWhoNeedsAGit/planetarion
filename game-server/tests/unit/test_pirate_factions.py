from backend.services.pirate_factions import (
    configured_pirate_usernames,
    is_pirate_username,
    select_primary_pirate_user,
)


class _U:
    def __init__(self, user_id: int, username: str):
        self.id = user_id
        self.username = username


def test_configured_pirate_usernames_defaults_when_unset():
    names = configured_pirate_usernames(config={"PIRATE_FACTION_USERNAMES": ""})
    assert "pirates" in names
    assert "pirates_red" in names
    assert "pirates_black" in names


def test_is_pirate_username_uses_configured_list():
    cfg = {"PIRATE_FACTION_USERNAMES": "pirates, pirates_ember"}
    assert is_pirate_username("pirates_ember", config=cfg) is True
    assert is_pirate_username("pirates", config=cfg) is True
    assert is_pirate_username("alpha", config=cfg) is False


def test_select_primary_pirate_user_prefers_canonical_pirates():
    users = [_U(12, "pirates_red"), _U(5, "pirates"), _U(7, "pirates_black")]
    primary = select_primary_pirate_user(users, config={"PIRATE_FACTION_USERNAMES": "pirates,pirates_red,pirates_black"})
    assert primary is not None
    assert primary.username == "pirates"
