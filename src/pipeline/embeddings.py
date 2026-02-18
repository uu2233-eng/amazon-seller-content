"""
向量化引擎

Pipeline 第 ② 步：将过滤后的内容转为向量表示。
支持两种 provider：
  - gemini: 使用 Google Gemini text-embedding-004（768 维）
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
        self.provider = pipe_config.get("provider", "gemini")
        self.batch_size = pipe_config.get("batch_size", 64)
        self.gemini_model = pipe_config.get("gemini_model", "text-embedding-004")
        self.local_model_name = pipe_config.get("local_model", "all-MiniLM-L6-v2")
        self.api_key = config.get("api_keys", {}).get("google_api_key", "")
        self._local_model = None

    def _get_local_model(self):
        if self._local_model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise RuntimeError(
                    "sentence-transformers not installed. "
                    "Set provider=gemini with a GOOGLE_API_KEY, "
                    "or install: pip install sentence-transformers"
                )
            logger.info(f"Loading local model: {self.local_model_name}")
            self._local_model = SentenceTransformer(self.local_model_name)
        return self._local_model

    def _embed_gemini(self, texts: list[str]) -> np.ndarray:
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            result = genai.embed_content(
                model=f"models/{self.gemini_model}",
                content=batch,
                task_type="RETRIEVAL_DOCUMENT",
            )
            all_embeddings.extend(result["embedding"])
            logger.debug(f"Gemini embedding batch {i // self.batch_size + 1} done")

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

        if self.provider == "gemini":
            if not self.api_key:
                logger.warning("Google API key missing, falling back to local model.")
                return self._embed_local(texts)
            return self._embed_gemini(texts)
        else:
            return self._embed_local(texts)

    def embed_contents(self, contents: list[RawContent]) -> np.ndarray:
        """将 RawContent 列表转为向量矩阵"""
        texts = [c.full_text for c in contents]
        return self.embed_texts(texts)
