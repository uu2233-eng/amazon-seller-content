"""
抓取任务 API

支持两种后台执行方式：
  1. Cloud Tasks (GCP 生产环境) — 通过 HTTP 回调异步执行，不怕超时
  2. 本地线程 (开发环境) — 当 Cloud Tasks 未配置时 fallback
"""

from __future__ import annotations

import json
import logging
import os
import threading

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from api.database import get_db, SessionLocal
from api.models import DBScrapeJob
from api.schemas import JobCreate, JobOut
from api.services.pipeline_service import run_pipeline_job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["Scrape Jobs"])

# Cloud Tasks 配置（通过环境变量）
GCP_PROJECT = os.getenv("GCP_PROJECT", "")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GCP_QUEUE = os.getenv("GCP_TASKS_QUEUE", "pipeline-jobs")
CLOUD_RUN_URL = os.getenv("CLOUD_RUN_BACKEND_URL", "")


def _dispatch_to_cloud_tasks(job_id: int, payload: JobCreate):
    """将任务推送到 Cloud Tasks 队列"""
    from google.cloud import tasks_v2

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(GCP_PROJECT, GCP_LOCATION, GCP_QUEUE)

    task_body = {
        "job_id": job_id,
        "audience_id": payload.audience_id,
        "output_formats": payload.output_formats,
        "max_topics": payload.max_topics,
    }

    task = tasks_v2.Task(
        http_request=tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url=f"{CLOUD_RUN_URL}/api/jobs/execute",
            headers={"Content-Type": "application/json"},
            body=json.dumps(task_body).encode(),
        ),
    )

    # Cloud Tasks 自动重试，最大执行 30 分钟
    task.dispatch_deadline = {"seconds": 1800}

    created = client.create_task(parent=parent, task=task)
    logger.info(f"Cloud Task created: {created.name}")


def _dispatch_to_thread(job_id: int, payload: JobCreate):
    """开发环境 fallback：用线程执行"""
    def _run():
        session = SessionLocal()
        try:
            run_pipeline_job(
                db=session,
                job_id=job_id,
                audience_id=payload.audience_id,
                output_formats=payload.output_formats,
                max_topics=payload.max_topics,
            )
        finally:
            session.close()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


@router.post("/", response_model=JobOut, status_code=201)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    """创建抓取任务 → 自动分发到 Cloud Tasks 或本地线程"""
    job = DBScrapeJob(
        audience_id=payload.audience_id,
        status="pending",
        sources_config={
            "output_formats": payload.output_formats,
            "max_topics": payload.max_topics,
        },
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if GCP_PROJECT and CLOUD_RUN_URL:
        try:
            _dispatch_to_cloud_tasks(job.id, payload)
            logger.info(f"Job {job.id} dispatched to Cloud Tasks")
        except Exception as e:
            logger.error(f"Cloud Tasks dispatch failed, falling back to thread: {e}")
            _dispatch_to_thread(job.id, payload)
    else:
        _dispatch_to_thread(job.id, payload)

    return job


@router.post("/execute")
async def execute_job(request: Request, db: Session = Depends(get_db)):
    """
    Cloud Tasks 回调端点。

    Cloud Tasks 通过 HTTP POST 调用此接口执行实际的管道任务。
    Cloud Run 会为此请求分配最长 60 分钟超时。
    """
    body = await request.json()

    job_id = body["job_id"]
    logger.info(f"Executing job {job_id} via Cloud Tasks callback")

    run_pipeline_job(
        db=db,
        job_id=job_id,
        audience_id=body["audience_id"],
        output_formats=body["output_formats"],
        max_topics=body.get("max_topics", 10),
    )

    return {"status": "completed", "job_id": job_id}


@router.get("/", response_model=list[JobOut])
def list_jobs(
    audience_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(DBScrapeJob)
    if audience_id:
        query = query.filter(DBScrapeJob.audience_id == audience_id)
    if status:
        query = query.filter(DBScrapeJob.status == status)
    return query.order_by(DBScrapeJob.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(DBScrapeJob).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job
