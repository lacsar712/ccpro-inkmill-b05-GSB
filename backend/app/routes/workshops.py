from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.database import SessionLocal
from app.models.mill import Mill
from app.models.user import User
from app.models.workshop import Workshop
from app.serializers import workshop_json
from app.utils import error

bp = Blueprint("workshops", __name__, url_prefix="/api/workshops")


def _current_user(db) -> User | None:
    username = get_jwt_identity()
    if not username:
        return None
    return db.query(User).filter(User.username == username).first()


def _require_admin(db):
    user = _current_user(db)
    if not user or user.role != "admin":
        return error("仅管理员可归档或解档车间", 403)
    return None


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes")


@bp.get("")
@jwt_required()
def list_workshops():
    include_archived = _truthy(request.args.get("includeArchived"))
    db = SessionLocal()
    try:
        query = db.query(Workshop)
        if not include_archived:
            query = query.filter(Workshop.archived.is_(False))
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
    db = SessionLocal()
    try:
        forbidden = _require_admin(db)
        if forbidden:
            return forbidden

        row = db.get(Workshop, item_id)
        if not row:
            return error("车间不存在", 404)

        row.archived = True
        db.commit()
        db.refresh(row)
        mill_count = (
            db.query(Mill).filter(Mill.workshop_id == item_id).count()
        )
        return jsonify({**workshop_json(row), "millCount": mill_count})
    finally:
        db.close()


@bp.post("/<int:item_id>/unarchive")
@jwt_required()
def unarchive_workshop(item_id: int):
    db = SessionLocal()
    try:
        forbidden = _require_admin(db)
        if forbidden:
            return forbidden

        row = db.get(Workshop, item_id)
        if not row:
            return error("车间不存在", 404)

        row.archived = False
        db.commit()
        db.refresh(row)
        mill_count = (
            db.query(Mill).filter(Mill.workshop_id == item_id).count()
        )
        return jsonify({**workshop_json(row), "millCount": mill_count})
    finally:
        db.close()


@bp.delete("/<int:item_id>")
@jwt_required()
def delete_workshop(item_id: int):
    # 车间只允许归档，不做物理删除，避免级联抹掉机台/取样/遍次
    return error("车间不支持物理删除，请使用归档功能", 405)
