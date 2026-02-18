"""
数据库模型 (Supabase / PostgreSQL + pgvector)

数据关系：
  Audience → Keyword → RawContent → FilteredContent → Embedding → TopicCluster → ContentIdea

向量列说明：
  contents.embedding — 存储 content 的 embedding 向量（pgvector vector 类型）
  仅在 PostgreSQL 下生效，SQLite 开发环境自动跳过向量列。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY as PG_ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from .database import Base, is_postgres

# pgvector 类型：仅在 PostgreSQL (Supabase) 环境下使用
_vector_type = None
try:
    from pgvector.sqlalchemy import Vector
    _vector_type = Vector
except ImportError:
    pass

# Supabase 用 JSONB（更快的索引），SQLite 用普通 JSON
_JsonCol = JSONB if is_postgres() else JSON

# embedding 维度：Gemini text-embedding-004 = 768, all-MiniLM-L6-v2 = 384
EMBEDDING_DIM = 768


def _embedding_column():
    """根据环境返回合适的向量列类型"""
    if is_postgres() and _vector_type:
        return Column("embedding", _vector_type(EMBEDDING_DIM), nullable=True)
    return Column("embedding_json", Text, nullable=True, default=None)


# ─────────────────────────────────────────────────
# Audience (受众)
# ─────────────────────────────────────────────────

class DBAudience(Base):
    __tablename__ = "audiences"

    id = Column(String(64), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    core_keywords = Column(_JsonCol, default=list)
    extended_keywords = Column(_JsonCol, default=list)
    subreddits = Column(_JsonCol, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    jobs = relationship("DBScrapeJob", back_populates="audience")


# ─────────────────────────────────────────────────
# ScrapeJob (抓取任务)
# ─────────────────────────────────────────────────

class DBScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audience_id = Column(String(64), ForeignKey("audiences.id"), nullable=False)
    status = Column(String(20), default="pending", index=True)
    sources_config = Column(_JsonCol, default=dict)
    total_raw = Column(Integer, default=0)
    total_filtered = Column(Integer, default=0)
    total_deduped = Column(Integer, default=0)
    total_clusters = Column(Integer, default=0)
    total_ideas = Column(Integer, default=0)
    error_message = Column(Text, default="")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    audience = relationship("DBAudience", back_populates="jobs")
    contents = relationship("DBContent", back_populates="job", cascade="all, delete-orphan")
    clusters = relationship("DBTopicCluster", back_populates="job", cascade="all, delete-orphan")
    ideas = relationship("DBContentIdea", back_populates="job", cascade="all, delete-orphan")


# ─────────────────────────────────────────────────
# Content (原始/过滤后的内容 + embedding 向量)
# ─────────────────────────────────────────────────

class DBContent(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("scrape_jobs.id"), nullable=False, index=True)
    content_hash = Column(String(32), index=True)
    source = Column(String(30), nullable=False, index=True)
    content_type = Column(String(30))
    title = Column(String(500))
    body = Column(Text, default="")
    url = Column(String(1000))
    author = Column(String(200), default="")
    published_at = Column(DateTime, nullable=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    tags = Column(_JsonCol, default=list)
    extra = Column(_JsonCol, default=dict)
    keyword_hits = Column(Integer, default=0)
    is_duplicate = Column(Boolean, default=False)
    cluster_id = Column(Integer, ForeignKey("topic_clusters.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("DBScrapeJob", back_populates="contents")
    cluster = relationship("DBTopicCluster", back_populates="contents")


# pgvector 向量列 — 通过 DDL 事件添加（避免 SQLite 报错）
if is_postgres() and _vector_type:
    DBContent.embedding = Column("embedding", _vector_type(EMBEDDING_DIM), nullable=True)
else:
    DBContent.embedding_json = Column("embedding_json", Text, nullable=True)


# ─────────────────────────────────────────────────
# TopicCluster (话题簇)
# ─────────────────────────────────────────────────

class DBTopicCluster(Base):
    __tablename__ = "topic_clusters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("scrape_jobs.id"), nullable=False, index=True)
    cluster_index = Column(Integer)
    label = Column(String(300), default="")
    size = Column(Integer, default=0)
    total_engagement = Column(Float, default=0.0)
    avg_engagement = Column(Float, default=0.0)
    sources = Column(_JsonCol, default=list)
    top_titles = Column(_JsonCol, default=list)
    representative_title = Column(String(500), default="")
    representative_body = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("DBScrapeJob", back_populates="clusters")
    contents = relationship("DBContent", back_populates="cluster")
    ideas = relationship("DBContentIdea", back_populates="cluster", cascade="all, delete-orphan")


# ─────────────────────────────────────────────────
# ContentIdea (生成的内容创意)
# ─────────────────────────────────────────────────

class DBContentIdea(Base):
    __tablename__ = "content_ideas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("scrape_jobs.id"), nullable=False, index=True)
    cluster_id = Column(Integer, ForeignKey("topic_clusters.id"), nullable=False)
    audience_id = Column(String(64), index=True)
    format_type = Column(String(30), index=True)
    topic_label = Column(String(300))
    generated_content = Column(Text, default="")
    source_urls = Column(_JsonCol, default=list)
    is_favorite = Column(Boolean, default=False, index=True)
    is_published = Column(Boolean, default=False)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("DBScrapeJob", back_populates="ideas")
    cluster = relationship("DBTopicCluster", back_populates="ideas")
