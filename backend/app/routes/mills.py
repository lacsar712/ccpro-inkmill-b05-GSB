from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.mill import MILL_STATUSES, Mill
from app.models.workshop import Workshop
from app.serializers import mill_json
from app.utils import error

bp = Blueprint("mills", __name__, url_prefix="/api/mills")


def _check_fields(body: dict) -> tuple[int | None, str | None]:
    workshop_id = int(body.get("workshopId") or 0)
    if workshop_id <= 0:
        return None, "请选择所属车间"

    mill_code = str(body.get("millCode", "")).strip()
    if not mill_code:
        return None, "研磨机编号不能为空"

    pigment_base = str(body.get("pigmentBase", "")).strip()
    if not pigment_base:
        return None, "色浆基料不能为空"

    status = str(body.get("status") or "idle")
    if status not in MILL_STATUSES:
        return None, "状态无效，应为 grinding / idle / wash"

    return workshop_id, None


@bp.get("")
@jwt_required()
def list_mills():
    db = SessionLocal()
    try:
        rows = db.query(Mill).order_by(Mill.id.desc()).all()
        return jsonify([mill_json(r) for r in rows])
    finally:
        db.close()


@bp.post("")
@jwt_required()
def create_mill():
    body = request.get_json(silent=True) or {}
    workshop_id, field_err = _check_fields(body)
    if field_err:
        return error(field_err, 400)

    db = SessionLocal()
    try:
        workshop = db.get(Workshop, workshop_id)
        if not workshop:
            return error("所属车间不存在", 400)
        if workshop.archived:
            return error("车间已归档，禁止新建研磨机", 409)

        row = Mill(
            workshop_id=workshop_id,
            mill_code=str(body["millCode"]).strip(),
            pigment_base=str(body["pigmentBase"]).strip(),
            bowl_liters=Decimal(str(body.get("bowlLiters", 0))),
            status=str(body.get("status") or "idle"),
        )
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return error("该车间下研磨机编号已存在", 400)
        db.refresh(row)
        return jsonify(mill_json(row)), 201
    finally:
        db.close()


@bp.put("/<int:item_id>")
@jwt_required()
def update_mill(item_id: int):
    body = request.get_json(silent=True) or {}
    workshop_id, field_err = _check_fields(body)
    if field_err:
        return error(field_err, 400)

    db = SessionLocal()
    try:
        row = db.get(Mill, item_id)
        if not row:
            return error("研磨机不存在", 404)

        workshop = db.get(Workshop, workshop_id)
        if not workshop:
            return error("所属车间不存在", 400)
        # 仅拦截“改归属到归档车间”；机台留在原归档车间内编辑其他字段不受此限
        if workshop.archived and row.workshop_id != workshop_id:
            return error("车间已归档，禁止把研磨机归属变更到该车间", 409)

        row.workshop_id = workshop_id
        row.mill_code = str(body["millCode"]).strip()
        row.pigment_base = str(body["pigmentBase"]).strip()
        row.bowl_liters = Decimal(str(body.get("bowlLiters", 0)))
        row.status = str(body.get("status") or "idle")
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return error("该车间下研磨机编号已存在", 400)
        db.refresh(row)
        return jsonify(mill_json(row))
    finally:
        db.close()


@bp.delete("/<int:item_id>")
@jwt_required()
def delete_mill(item_id: int):
    db = SessionLocal()
    try:
        row = db.get(Mill, item_id)
        if not row:
            return error("研磨机不存在", 404)
        db.delete(row)
        db.commit()
        return jsonify({"ok": True})
    finally:
        db.close()
