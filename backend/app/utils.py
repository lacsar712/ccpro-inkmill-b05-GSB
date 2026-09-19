from datetime import datetime

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from app.database import SessionLocal
from app.models.user import User


def error(message: str, status: int = 400):
    return jsonify({"message": message}), status


def current_user() -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.username == get_jwt_identity()).first()
    finally:
        db.close()


def is_admin() -> bool:
    user = current_user()
    return bool(user and user.role == "admin")


def normalize_datetime(value: str) -> datetime:
    value = (value or "").strip()
    if not value:
        return datetime.now()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value.replace("Z", "")[:26], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now()


def dt_to_json(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")
