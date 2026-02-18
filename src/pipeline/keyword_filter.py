"""
关键词粗筛过滤器

Pipeline 第 ① 步：用关键词库对原始内容做快速粗筛。
目的：减少下游 embedding 成本、降低噪声。
"""

from __future__ import annotations

import logging
import re

from src.scrapers.base import RawContent

logger = logging.getLogger(__name__)


class KeywordFilter:
    """
    基于关键词命中的内容过滤器。

    过滤逻辑：
    1. 将内容 full_text 转小写
    2. 检查关键词命中数量
    3. 达到 min_hits 阈值即保留
    """

    def __init__(self, keywords: list[str], min_hits: int = 1, case_sensitive: bool = False):
        self.case_sensitive = case_sensitive
        self.min_hits = min_hits

        if case_sensitive:
            self.patterns = [re.compile(re.escape(kw)) for kw in keywords]
        else:
            self.patterns = [
                re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords
            ]

        self._keywords = keywords
        logger.info(f"KeywordFilter initialized with {len(keywords)} keywords, min_hits={min_hits}")

    def score(self, content: RawContent) -> int:
        """计算内容的关键词命中数"""
        text = content.full_text
        hits = 0
        for pattern in self.patterns:
            if pattern.search(text):
                hits += 1
        return hits

    def filter(self, contents: list[RawContent]) -> list[RawContent]:
        """过滤内容，返回命中关键词数 >= min_hits 的内容"""
        filtered = []
        for content in contents:
            hit_count = self.score(content)
            if hit_count >= self.min_hits:
                content.extra["keyword_hits"] = hit_count
                filtered.append(content)

        logger.info(
            f"KeywordFilter: {len(contents)} → {len(filtered)} "
            f"(filtered out {len(contents) - len(filtered)})"
        )
        return filtered

    def filter_with_scores(
        self, contents: list[RawContent]
    ) -> list[tuple[RawContent, int]]:
        """返回 (内容, 命中数) 的列表，按命中数降序"""
        scored = []
        for content in contents:
            hit_count = self.score(content)
            if hit_count >= self.min_hits:
                content.extra["keyword_hits"] = hit_count
                scored.append((content, hit_count))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
