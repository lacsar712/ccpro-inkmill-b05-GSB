from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.mill import Mill
from app.models.workshop import Workshop
from app.serializers import workshop_json
from app.utils import error, is_admin

bp = Blueprint("workshops", __name__, url_prefix="/api/workshops")


@bp.get("")
@jwt_required()
def list_workshops():
    include_archived = request.args.get("includeArchived") == "1"
    db = SessionLocal()
    try:
        query = db.query(Workshop)
        if not include_archived:
            query = query.filter(Workshop.archived == False)  # noqa: E712
        rows = query.order_by(Workshop.id.desc()).all()
        return jsonify([workshop_json(r) for r in rows])
    finally:
        db.close()


@bp.post("")
@jwt_required()
def create_workshop():
    body = request.get_json(silent=True) or {}
    name = str(body.get("name", "")).strip()
    if not name:
        return error("车间名称不能为空", 400)

    site = str(body.get("site", "")).strip() or None
    notes = str(body.get("notes", "")).strip() or None

    db = SessionLocal()
    try:
        row = Workshop(name=name, site=site, notes=notes)
        db.add(row)
        db.commit()
        db.refresh(row)
        return jsonify(workshop_json(row)), 201
    finally:
        db.close()


@bp.put("/<int:item_id>")
@jwt_required()
def update_workshop(item_id: int):
    db = SessionLocal()
    try:
        row = db.get(Workshop, item_id)
        if not row:
            return error("车间不存在", 404)

        body = request.get_json(silent=True) or {}
        name = str(body.get("name", "")).strip()
        if not name:
            return error("车间名称不能为空", 400)

        row.name = name
        row.site = str(body.get("site", "")).strip() or None
        row.notes = str(body.get("notes", "")).strip() or None
        db.commit()
        db.refresh(row)
        return jsonify(workshop_json(row))
    finally:
        db.close()


@bp.post("/<int:item_id>/archive")
@jwt_required()
def archive_workshop(item_id: int):
    if not is_admin():
        return error("仅管理员可归档车间", 403)

    db = SessionLocal()
    try:
        row = db.get(Workshop, item_id)
        if not row:
            return error("车间不存在", 404)
        row.archived = True
        mill_count = db.scalar(
            select(func.count()).select_from(Mill).where(Mill.workshop_id == item_id)
        ) or 0
        db.commit()
        db.refresh(row)
        return jsonify({**workshop_json(row), "millCount": mill_count})
    finally:
        db.close()


@bp.post("/<int:item_id>/unarchive")
@jwt_required()
def unarchive_workshop(item_id: int):
    if not is_admin():
        return error("仅管理员可解档车间", 403)

    db = SessionLocal()
    try:
        row = db.get(Workshop, item_id)
        if not row:
            return error("车间不存在", 404)
        row.archived = False
        db.commit()
        db.refresh(row)
        return jsonify(workshop_json(row))
    finally:
        db.close()
