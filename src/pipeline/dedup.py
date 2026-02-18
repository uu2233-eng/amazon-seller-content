"""
语义去重模块

Pipeline 第 ② 步（续）：基于余弦相似度去除重复/近似内容。
目的：
  - 合并同义表达
  - 合并重复讨论
  - 防止爆词重复刷屏
"""

from __future__ import annotations

import logging

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.scrapers.base import RawContent

logger = logging.getLogger(__name__)


class Deduplicator:

    def __init__(self, similarity_threshold: float = 0.88):
        self.similarity_threshold = similarity_threshold

    def deduplicate(
        self,
        contents: list[RawContent],
        embeddings: np.ndarray,
    ) -> tuple[list[RawContent], np.ndarray]:
        """
        去除重复内容。

        算法：
        1. 计算全量 cosine similarity 矩阵
        2. 遍历每对内容，若相似度 > 阈值，保留 engagement_score 更高的那条
        3. 返回去重后的内容和对应的向量

        Returns:
            (去重后的内容列表, 去重后的向量矩阵)
        """
        if len(contents) <= 1:
            return contents, embeddings

        logger.info(
            f"Dedup: computing similarity for {len(contents)} items "
            f"(threshold={self.similarity_threshold})"
        )

        sim_matrix = cosine_similarity(embeddings)
        n = len(contents)
        to_remove: set[int] = set()

        for i in range(n):
            if i in to_remove:
                continue
            for j in range(i + 1, n):
                if j in to_remove:
                    continue
                if sim_matrix[i][j] >= self.similarity_threshold:
                    # 保留互动分更高的那条
                    if contents[i].engagement_score >= contents[j].engagement_score:
                        to_remove.add(j)
                        contents[i].extra.setdefault("merged_urls", []).append(
                            contents[j].url
                        )
                    else:
                        to_remove.add(i)
                        contents[j].extra.setdefault("merged_urls", []).append(
                            contents[i].url
                        )
                        break  # i 被移除，不需要继续比较

        keep_indices = [i for i in range(n) if i not in to_remove]
        deduped_contents = [contents[i] for i in keep_indices]
        deduped_embeddings = embeddings[keep_indices]

        logger.info(
            f"Dedup: {n} → {len(deduped_contents)} "
            f"(removed {len(to_remove)} duplicates)"
        )

        return deduped_contents, deduped_embeddings
