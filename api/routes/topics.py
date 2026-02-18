"""话题簇 API"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import get_db, is_postgres
from api.models import DBTopicCluster, DBContent
from api.schemas import TopicClusterOut, ContentOut
from api.services.vector_store import VectorStore

router = APIRouter(prefix="/topics", tags=["Topics"])


@router.get("/", response_model=list[TopicClusterOut])
def list_topics(
    job_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(DBTopicCluster)
    if job_id:
        query = query.filter(DBTopicCluster.job_id == job_id)
    return (
        query.order_by(DBTopicCluster.total_engagement.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{topic_id}", response_model=TopicClusterOut)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(DBTopicCluster).get(topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found")
    return topic


@router.get("/{topic_id}/contents", response_model=list[ContentOut])
def get_topic_contents(topic_id: int, db: Session = Depends(get_db)):
    """获取话题簇下的所有内容"""
    topic = db.query(DBTopicCluster).get(topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found")
    contents = (
        db.query(DBContent)
        .filter(DBContent.cluster_id == topic_id)
        .order_by(DBContent.engagement_score.desc())
        .all()
    )
    return contents


# ── 语义搜索 (pgvector) ──

class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 10
    threshold: float = 0.75
    job_id: int | None = None


class SimilarContentItem(BaseModel):
    id: int
    title: str
    url: str
    source: str
    engagement_score: float
    similarity: float


@router.post("/search/semantic", response_model=list[SimilarContentItem])
def semantic_search(
    payload: SemanticSearchRequest,
    db: Session = Depends(get_db),
):
    """
    语义搜索（Supabase pgvector）

    输入自然语言查询，返回向量相似度最高的内容。
    需要 Supabase (PostgreSQL + pgvector) 环境。
    """
    if not is_postgres():
        raise HTTPException(400, "Semantic search requires PostgreSQL (Supabase) with pgvector")

    from src.pipeline.embeddings import EmbeddingEngine
    from src.utils.helpers import load_config

    config = load_config()
    embedder = EmbeddingEngine(config)
    query_vec = embedder.embed_texts([payload.query])[0]

    store = VectorStore(db)
    results = store.find_similar(
        query_embedding=query_vec,
        limit=payload.limit,
        threshold=payload.threshold,
        job_id=payload.job_id,
    )
    return results
