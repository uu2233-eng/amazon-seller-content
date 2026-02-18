"""
向量化引擎

Pipeline 第 ② 步：将过滤后的内容转为向量表示。
支持两种 provider：
  - openai: 使用 OpenAI text-embedding-3-small（付费但效果好）
  - local: 使用 sentence-transformers all-MiniLM-L6-v2（免费本地运行）
"""

from __future__ import annotations

import logging

import numpy as np

from src.scrapers.base import RawContent

logger = logging.getLogger(__name__)


class EmbeddingEngine:

    def __init__(self, config: dict):
        pipe_config = config.get("pipeline", {}).get("embedding", {})
        self.provider = pipe_config.get("provider", "openai")
        self.batch_size = pipe_config.get("batch_size", 64)
        self.openai_model = pipe_config.get("openai_model", "text-embedding-3-small")
        self.local_model_name = pipe_config.get("local_model", "all-MiniLM-L6-v2")
        self.api_key = config.get("api_keys", {}).get("openai_api_key", "")
        self._local_model = None

    def _get_local_model(self):
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading local model: {self.local_model_name}")
            self._local_model = SentenceTransformer(self.local_model_name)
        return self._local_model

    def _embed_openai(self, texts: list[str]) -> np.ndarray:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            response = client.embeddings.create(
                model=self.openai_model,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            logger.debug(f"OpenAI embedding batch {i // self.batch_size + 1} done")

        return np.array(all_embeddings)

    def _embed_local(self, texts: list[str]) -> np.ndarray:
        model = self._get_local_model()
        embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        return np.array(embeddings)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """将文本列表转为向量矩阵"""
        if not texts:
            return np.array([])

        logger.info(f"Embedding {len(texts)} texts using provider={self.provider}")

        if self.provider == "openai":
            if not self.api_key:
                logger.warning("OpenAI API key missing, falling back to local model.")
                return self._embed_local(texts)
            return self._embed_openai(texts)
        else:
            return self._embed_local(texts)

    def embed_contents(self, contents: list[RawContent]) -> np.ndarray:
        """将 RawContent 列表转为向量矩阵"""
        texts = [c.full_text for c in contents]
        return self.embed_texts(texts)
