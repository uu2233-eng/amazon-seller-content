"""
抓取基础类与数据模型

RawContent 是所有数据源统一的原始内容结构。
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawContent:
    """统一的原始内容数据结构"""
    source: str                          # youtube / reddit / rss / trends
    content_type: str                    # video / post / article / trend
    title: str
    body: str                            # 正文/描述/自述
    url: str
    author: str = ""
    published_at: datetime | None = None
    scraped_at: datetime = field(default_factory=datetime.utcnow)

    # 互动指标（不同来源含义不同）
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0

    # 附加元数据
    tags: list[str] = field(default_factory=list)
    thumbnail_url: str = ""
    language: str = "en"
    extra: dict = field(default_factory=dict)

    @property
    def content_id(self) -> str:
        raw = f"{self.source}:{self.url}"
        return hashlib.md5(raw.encode()).hexdigest()

    @property
    def full_text(self) -> str:
        """用于后续 embedding 的完整文本"""
        parts = [self.title]
        if self.body:
            parts.append(self.body)
        if self.tags:
            parts.append(" ".join(self.tags))
        return " ".join(parts)

    @property
    def engagement_score(self) -> float:
        """综合互动分（归一化后用于排序）"""
        return (
            self.views * 0.1
            + self.likes * 1.0
            + self.comments * 2.0
            + self.shares * 3.0
        )

    def to_dict(self) -> dict:
        return {
            "content_id": self.content_id,
            "source": self.source,
            "content_type": self.content_type,
            "title": self.title,
            "body": self.body[:500],
            "url": self.url,
            "author": self.author,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "tags": self.tags,
            "engagement_score": self.engagement_score,
        }


class BaseScraper(ABC):
    """抓取器基类"""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def scrape(self, keywords: list[str]) -> list[RawContent]:
        """根据关键词列表抓取内容"""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        ...
