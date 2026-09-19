"""幂等的轻量启动迁移（无 Alembic）。

旧库补列：workshops.archived，TINYINT(1) NOT NULL DEFAULT 0。
归档不物理删除车间，也不级联抹掉机台/取样/遍次。
"""

from sqlalchemy import text

from app.database import engine


def migrate() -> None:
    with engine.begin() as conn:
        exists = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = DATABASE() "
                "AND table_name = 'workshops' AND column_name = 'archived'"
            )
        ).scalar()
        if not exists:
            conn.execute(
                text(
                    "ALTER TABLE workshops "
                    "ADD COLUMN archived TINYINT(1) NOT NULL DEFAULT 0"
                )
            )
            print("Added workshops.archived column.")
        else:
            print("workshops.archived already present.")


if __name__ == "__main__":
    migrate()
