"""
FastAPI 应用入口

启动方式：
  uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import init_db, is_postgres
from api.routes import audiences, jobs, topics, content, dashboard

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Amazon Seller Content Engine",
    description="热点内容抓取 & AI 内容创意生成引擎 · Supabase + pgvector",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

_cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if os.getenv("ALLOWED_ORIGINS"):
    _cors_origins.extend(os.getenv("ALLOWED_ORIGINS", "").split(","))
if os.getenv("CLOUD_RUN_FRONTEND_URL"):
    _cors_origins.append(os.getenv("CLOUD_RUN_FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(audiences.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(topics.router, prefix="/api")
app.include_router(content.router, prefix="/api")


@app.on_event("startup")
def on_startup():
    # 加载 .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # 初始化数据库（Supabase PostgreSQL 或本地 SQLite）
    init_db()

    db_type = "Supabase (PostgreSQL + pgvector)" if is_postgres() else "SQLite (local dev)"
    logger.info(f"Database: {db_type}")

    # 可选：初始化 Supabase Client
    if is_postgres():
        from api.supabase_client import get_supabase_client
        client = get_supabase_client()
        if client:
            logger.info("Supabase Client ready")


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "Amazon Seller Content Engine",
        "database": "supabase" if is_postgres() else "sqlite",
        "vector_search": is_postgres(),
    }
