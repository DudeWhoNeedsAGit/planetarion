import os


def test_admin_db_snapshot_and_restore(app):
    # Use the dev admin token path (no JWT needed).
    os.environ["PLANETARION_DEV_ADMIN_TOKEN"] = "test-token"

    client = app.test_client()

    with app.app_context():
        from backend.database import db
        from backend.models import User
        import bcrypt

        # Seed a known user so we can verify restore.
        password_hash = bcrypt.hashpw("pw".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        baseline = User(username="baseline_user", email="baseline@example.com", password_hash=password_hash)
        db.session.add(baseline)
        db.session.commit()

    snap = client.post(
        "/api/admin/db/snapshot",
        json={"overwrite": True},
        headers={"X-Planetarion-Dev-Token": "test-token"},
    )
    assert snap.status_code == 200

    with app.app_context():
        from backend.database import db
        from backend.models import User
        import bcrypt

        password_hash = bcrypt.hashpw("pw".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        extra = User(username="extra_user", email="extra@example.com", password_hash=password_hash)
        db.session.add(extra)
        db.session.commit()
        assert User.query.filter_by(username="extra_user").first() is not None

    restore = client.post(
        "/api/admin/db/restore",
        json={},
        headers={"X-Planetarion-Dev-Token": "test-token"},
    )
    assert restore.status_code == 200

    with app.app_context():
        from backend.database import db
        from backend.models import User

        # Ensure we re-open a fresh connection after the restore.
        db.session.remove()
        assert User.query.filter_by(username="baseline_user").first() is not None
        assert User.query.filter_by(username="extra_user").first() is None

