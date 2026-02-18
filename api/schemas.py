"""
Pydantic 数据校验模型（API 请求/响应）
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# ── Audience ──

class AudienceOut(BaseModel):
    id: str
    name: str
    description: str
    core_keywords: list[str]
    extended_keywords: list[str]
    subreddits: list[str]
    is_active: bool
    keyword_count: int = 0

    model_config = {"from_attributes": True}


class AudienceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    core_keywords: list[str] | None = None
    extended_keywords: list[str] | None = None
    is_active: bool | None = None


# ── Scrape Job ──

class JobCreate(BaseModel):
    audience_id: str
    output_formats: list[str] = Field(
        default=["article", "short_video", "long_video", "image_prompt", "social_post"]
    )
    max_topics: int = Field(default=10, ge=1, le=50)


class JobOut(BaseModel):
    id: int
    audience_id: str
    status: str
    total_raw: int
    total_filtered: int
    total_deduped: int
    total_clusters: int
    total_ideas: int
    error_message: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Content ──

class ContentOut(BaseModel):
    id: int
    source: str
    content_type: str
    title: str
    body: str
    url: str
    author: str
    published_at: datetime | None
    views: int
    likes: int
    comments_count: int
    engagement_score: float
    tags: list[str]
    keyword_hits: int
    is_duplicate: bool
    cluster_id: int | None

    model_config = {"from_attributes": True}


# ── Topic Cluster ──

class TopicClusterOut(BaseModel):
    id: int
    job_id: int
    cluster_index: int
    label: str
    size: int
    total_engagement: float
    avg_engagement: float
    sources: list[str]
    top_titles: list[str]
    representative_title: str
    representative_body: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Content Idea ──

class ContentIdeaOut(BaseModel):
    id: int
    job_id: int
    cluster_id: int
    audience_id: str
    format_type: str
    topic_label: str
    generated_content: str
    source_urls: list[str]
    is_favorite: bool
    is_published: bool
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentIdeaUpdate(BaseModel):
    is_favorite: bool | None = None
    is_published: bool | None = None
    notes: str | None = None
    generated_content: str | None = None


# ── Dashboard Stats ──

class DashboardStats(BaseModel):
    total_jobs: int
    total_contents: int
    total_clusters: int
    total_ideas: int
    active_audiences: int
    recent_jobs: list[JobOut]
    top_topics: list[TopicClusterOut]


# ── Generic ──

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int
