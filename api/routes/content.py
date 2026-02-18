"""内容创意 API"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import DBContentIdea
from api.schemas import ContentIdeaOut, ContentIdeaUpdate

router = APIRouter(prefix="/ideas", tags=["Content Ideas"])


@router.get("/", response_model=list[ContentIdeaOut])
def list_ideas(
    job_id: int | None = None,
    cluster_id: int | None = None,
    audience_id: str | None = None,
    format_type: str | None = None,
    is_favorite: bool | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(DBContentIdea)
    if job_id:
        query = query.filter(DBContentIdea.job_id == job_id)
    if cluster_id:
        query = query.filter(DBContentIdea.cluster_id == cluster_id)
    if audience_id:
        query = query.filter(DBContentIdea.audience_id == audience_id)
    if format_type:
        query = query.filter(DBContentIdea.format_type == format_type)
    if is_favorite is not None:
        query = query.filter(DBContentIdea.is_favorite == is_favorite)
    return (
        query.order_by(DBContentIdea.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{idea_id}", response_model=ContentIdeaOut)
def get_idea(idea_id: int, db: Session = Depends(get_db)):
    idea = db.query(DBContentIdea).get(idea_id)
    if not idea:
        raise HTTPException(404, "Content idea not found")
    return idea


@router.patch("/{idea_id}", response_model=ContentIdeaOut)
def update_idea(
    idea_id: int,
    payload: ContentIdeaUpdate,
    db: Session = Depends(get_db),
):
    """更新内容创意（收藏、标记已发布、修改内容、添加笔记）"""
    idea = db.query(DBContentIdea).get(idea_id)
    if not idea:
        raise HTTPException(404, "Content idea not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(idea, field, value)

    db.commit()
    db.refresh(idea)
    return idea


@router.get("/formats/available")
def available_formats():
    return {
        "formats": [
            {"id": "article", "name": "图文/博客文案", "icon": "📝"},
            {"id": "short_video", "name": "短视频脚本 (60s)", "icon": "🎬"},
            {"id": "long_video", "name": "长视频脚本 (8-12min)", "icon": "🎥"},
            {"id": "image_prompt", "name": "AI 图片 Prompt", "icon": "🖼️"},
            {"id": "social_post", "name": "社交媒体帖子", "icon": "📱"},
        ]
    }
