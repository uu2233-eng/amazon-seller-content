"""
Supabase (PostgreSQL) 数据库配置

连接方式（按优先级）：
  1. SUPABASE_DB_URL  — Supabase 项目的 PostgreSQL 直连地址（Transaction 模式）
  2. DATABASE_URL     — 任意 PostgreSQL 地址
  3. 兜底              — 本地 SQLite（仅开发用）

Supabase 连接字符串格式：
  postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
"""

from __future__ import annotations

import os
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger(__name__)

# ── 连接地址优先级 ──
DATABASE_URL = (
    os.getenv("SUPABASE_DB_URL")
    or os.getenv("DATABASE_URL")
    or "sqlite:///./data/content_engine.db"
)

_is_postgres = DATABASE_URL.startswith("postgresql")

if _is_postgres:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"options": "-c statement_timeout=30000"},
    )
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _enable_pgvector(conn):
    """在 Supabase PostgreSQL 上启用 pgvector 扩展"""
    try:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        logger.info("pgvector extension enabled")
    except Exception as e:
        logger.warning(f"Could not enable pgvector (may already exist): {e}")
        conn.rollback()


def init_db():
    """
    初始化数据库：
      - PostgreSQL: 启用 pgvector → 用 SQLAlchemy 建表
      - SQLite: 直接建表（不支持向量列，自动跳过）
    """
    import api.models  # noqa: F401 — 确保所有模型被导入

    if _is_postgres:
        with engine.connect() as conn:
            _enable_pgvector(conn)

    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized ({'PostgreSQL/Supabase' if _is_postgres else 'SQLite'})")


def is_postgres() -> bool:
    return _is_postgres
