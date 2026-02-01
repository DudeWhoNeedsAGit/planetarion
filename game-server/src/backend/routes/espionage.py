from datetime import datetime
import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.database import db
from backend.models import EspionageReport


espionage_bp = Blueprint("espionage", __name__, url_prefix="/api/espionage")


@espionage_bp.route("/reports", methods=["GET"])
@jwt_required()
def get_spy_reports():
    user_id = int(get_jwt_identity())
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    reports = (
        EspionageReport.query.filter_by(user_id=user_id)
        .order_by(EspionageReport.timestamp.desc(), EspionageReport.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    def serialize(r: EspionageReport):
        try:
            intel = json.loads(r.intel) if r.intel else {}
        except Exception:
            intel = {}
        return {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "fleet_id": r.fleet_id,
            "target_planet_id": r.target_planet_id,
            "target_user_id": r.target_user_id,
            "success": bool(r.success),
            "intel": intel,
        }

    return jsonify({"reports": [serialize(r) for r in reports], "limit": limit, "offset": offset})

