"""
向量存储服务 (Supabase pgvector)

功能：
  - 将 embedding 向量写入 contents 表的 embedding 列
  - 利用 pgvector 做语义相似度搜索（<=> 余弦距离）
  - 支持向量化去重（数据库内直接查询近似内容）

SQLite 环境下自动退化为 JSON 文本存储（不支持向量检索）。
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.database import is_postgres
from api.models import DBContent

logger = logging.getLogger(__name__)


class VectorStore:

    def __init__(self, db: Session):
        self.db = db
        self._is_pg = is_postgres()

    def store_embedding(self, content_id: int, embedding: np.ndarray):
        """存储单条 embedding"""
        if self._is_pg:
            self.db.execute(
                text("UPDATE contents SET embedding = :vec WHERE id = :id"),
                {"vec": embedding.tolist(), "id": content_id},
            )
        else:
            self.db.execute(
                text("UPDATE contents SET embedding_json = :vec WHERE id = :id"),
                {"vec": json.dumps(embedding.tolist()), "id": content_id},
            )

    def store_embeddings_batch(
        self,
        content_ids: list[int],
        embeddings: np.ndarray,
    ):
        """批量存储 embedding"""
        for i, cid in enumerate(content_ids):
            self.store_embedding(cid, embeddings[i])
        self.db.commit()
        logger.info(f"Stored {len(content_ids)} embeddings into database")

    def find_similar(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        threshold: float = 0.85,
        job_id: Optional[int] = None,
    ) -> list[dict]:
        """
        在 Supabase 中做向量相似度搜索。

        使用 pgvector 的 <=> 运算符（余弦距离），距离越小越相似。
        cosine_similarity = 1 - cosine_distance
        """
        if not self._is_pg:
            logger.warning("Vector search not available in SQLite mode")
            return []

        distance_threshold = 1 - threshold
        sql = """
            SELECT id, title, url, source, engagement_score,
                   1 - (embedding <=> :query_vec) AS similarity
            FROM contents
            WHERE embedding IS NOT NULL
              AND 1 - (embedding <=> :query_vec) >= :threshold
        """
        params: dict = {
            "query_vec": query_embedding.tolist(),
            "threshold": threshold,
        }

        if job_id is not None:
            sql += " AND job_id = :job_id"
            params["job_id"] = job_id

        sql += " ORDER BY similarity DESC LIMIT :limit"
        params["limit"] = limit

        result = self.db.execute(text(sql), params)
        return [dict(row._mapping) for row in result]

    def find_duplicates(
        self,
        content_id: int,
        threshold: float = 0.88,
        job_id: Optional[int] = None,
    ) -> list[dict]:
        """查找与指定内容语义重复的条目"""
        if not self._is_pg:
            return []

        sql = """
            SELECT c2.id, c2.title, c2.url,
                   1 - (c1.embedding <=> c2.embedding) AS similarity
            FROM contents c1, contents c2
            WHERE c1.id = :cid
              AND c2.id != :cid
              AND c1.embedding IS NOT NULL
              AND c2.embedding IS NOT NULL
              AND 1 - (c1.embedding <=> c2.embedding) >= :threshold
        """
        params: dict = {"cid": content_id, "threshold": threshold}

        if job_id is not None:
            sql += " AND c2.job_id = :job_id"
            params["job_id"] = job_id

        sql += " ORDER BY similarity DESC LIMIT 20"

        result = self.db.execute(text(sql), params)
        return [dict(row._mapping) for row in result]

    def create_ivfflat_index(self, lists: int = 100):
        """
        创建 IVFFlat 索引以加速向量搜索。
        建议在数据量 > 1000 条后运行一次。
        """
        if not self._is_pg:
            logger.warning("IVFFlat index only available on PostgreSQL")
            return

        try:
            self.db.execute(text(
                f"CREATE INDEX IF NOT EXISTS idx_contents_embedding "
                f"ON contents USING ivfflat (embedding vector_cosine_ops) "
                f"WITH (lists = {lists})"
            ))
            self.db.commit()
            logger.info(f"IVFFlat index created with lists={lists}")
        except Exception as e:
            logger.error(f"Failed to create IVFFlat index: {e}")
            self.db.rollback()
