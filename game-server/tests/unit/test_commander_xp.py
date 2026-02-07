import pytest

from backend.models import User
from backend.services.commander_xp import CommanderXPService, level_for_xp, xp_to_next_level, xp_progress


def test_xp_curve_is_monotonic():
    prev = 0
    for level in range(1, 30):
        need = xp_to_next_level(level)
        assert need > 0
        assert need >= prev
        prev = need


def test_level_for_xp_and_progress_basic():
    assert level_for_xp(0) == 1
    assert xp_progress(0)[0] == 0

    need_l1 = xp_to_next_level(1)
    assert level_for_xp(need_l1 - 1) == 1
    assert level_for_xp(need_l1) == 2


def test_award_xp_is_idempotent(db_session, sample_user):
    uid = int(sample_user.id)
    before_xp = int(getattr(sample_user, "commander_xp", 0) or 0)
    before_level = int(getattr(sample_user, "commander_level", 1) or 1)

    r1 = CommanderXPService.award_xp(
        user_id=uid,
        xp=123,
        source_type="combat",
        source_id="report:1:attacker",
    )
    assert r1 is not None
    assert r1.applied is True

    db_session.flush()

    u = User.query.get(uid)
    assert int(u.commander_xp or 0) == before_xp + 123
    assert int(u.commander_level or 1) >= before_level

    r2 = CommanderXPService.award_xp(
        user_id=uid,
        xp=999,
        source_type="combat",
        source_id="report:1:attacker",
    )
    assert r2 is not None
    assert r2.applied is False

    db_session.flush()
    u2 = User.query.get(uid)
    assert int(u2.commander_xp or 0) == before_xp + 123


def test_award_xp_ignores_pirates_user(db_session):
    pirates = User(username="pirates", email="pirates@example.com", password_hash="x")
    db_session.add(pirates)
    db_session.commit()

    res = CommanderXPService.award_xp(
        user_id=int(pirates.id),
        xp=500,
        source_type="combat",
        source_id="report:1:attacker",
    )
    assert res is None

