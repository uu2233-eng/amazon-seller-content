"""Dashboard 概览 API"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.database import get_db
from api.models import DBScrapeJob, DBContent, DBTopicCluster, DBContentIdea, DBAudience
from api.schemas import DashboardStats, JobOut, TopicClusterOut

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    total_jobs = db.query(func.count(DBScrapeJob.id)).scalar() or 0
    total_contents = db.query(func.count(DBContent.id)).scalar() or 0
    total_clusters = db.query(func.count(DBTopicCluster.id)).scalar() or 0
    total_ideas = db.query(func.count(DBContentIdea.id)).scalar() or 0
    active_audiences = db.query(func.count(DBAudience.id)).filter(
        DBAudience.is_active == True
    ).scalar() or 0

    recent_jobs = (
        db.query(DBScrapeJob)
        .order_by(DBScrapeJob.created_at.desc())
        .limit(5)
        .all()
    )
    top_topics = (
        db.query(DBTopicCluster)
        .order_by(DBTopicCluster.total_engagement.desc())
        .limit(10)
        .all()
    )

    return DashboardStats(
        total_jobs=total_jobs,
        total_contents=total_contents,
        total_clusters=total_clusters,
        total_ideas=total_ideas,
        active_audiences=active_audiences,
        recent_jobs=[JobOut.model_validate(j) for j in recent_jobs],
        top_topics=[TopicClusterOut.model_validate(t) for t in top_topics],
    )
