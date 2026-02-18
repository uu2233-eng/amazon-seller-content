"""
管道服务

封装完整的 抓取→过滤→向量化→去重→聚类→生成 流程，
作为后台任务运行，结果写入 Supabase (PostgreSQL)。

向量数据通过 VectorStore 写入 contents.embedding 列，
支持后续的语义搜索和去重查询。
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from api.models import DBScrapeJob, DBContent, DBTopicCluster, DBContentIdea
from api.services.vector_store import VectorStore
from src.audiences import AUDIENCES, Audience
from src.scrapers import YouTubeScraper, RedditScraper, RSSScraper, GoogleTrendsScraper
from src.scrapers.base import RawContent
from src.pipeline import KeywordFilter, EmbeddingEngine, Deduplicator, TopicClusterer
from src.generator import ContentGenerator
from src.utils.helpers import load_config

logger = logging.getLogger(__name__)


def run_pipeline_job(
    db: Session,
    job_id: int,
    audience_id: str,
    output_formats: list[str],
    max_topics: int = 10,
):
    """
    完整管道任务（后台线程运行）。

    1. 多源抓取
    2. 关键词过滤
    3. 向量化 + 写入 Supabase pgvector
    4. 语义去重
    5. 话题聚类
    6. 内容生成 → 写入数据库
    """
    job = db.query(DBScrapeJob).get(job_id)
    if not job:
        logger.error(f"Job {job_id} not found")
        return

    job.status = "running"
    job.started_at = datetime.utcnow()
    db.commit()

    vector_store = VectorStore(db)

    try:
        config = load_config()
        config.setdefault("generation", {})["output_formats"] = output_formats

        audience = AUDIENCES.get(audience_id)
        if not audience:
            raise ValueError(f"Unknown audience: {audience_id}")

        keywords = audience.all_keywords

        # ── 1. 多源抓取 ──
        logger.info(f"[Job {job_id}] Scraping for audience: {audience.name}")
        raw_contents = _scrape_all(config, keywords)
        job.total_raw = len(raw_contents)
        db.commit()
        logger.info(f"[Job {job_id}] Scraped {len(raw_contents)} raw items")

        # 保存原始内容到 Supabase
        db_content_map: dict[int, RawContent] = {}  # db_id → RawContent
        for rc in raw_contents:
            db_item = _raw_to_db(rc, job_id)
            db.add(db_item)
            db.flush()
            db_content_map[db_item.id] = rc
        db.commit()

        if not raw_contents:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.error_message = "No content found from any source."
            db.commit()
            return

        # ── 2. 关键词过滤 ──
        logger.info(f"[Job {job_id}] Keyword filtering...")
        filter_cfg = config.get("pipeline", {}).get("keyword_filter", {})
        kw_filter = KeywordFilter(
            keywords=keywords,
            min_hits=filter_cfg.get("min_keyword_hits", 1),
        )
        filtered = kw_filter.filter(raw_contents)
        job.total_filtered = len(filtered)
        db.commit()

        if not filtered:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.error_message = "No content passed keyword filter."
            db.commit()
            return

        # ── 3. 向量化 + 写入 Supabase ──
        logger.info(f"[Job {job_id}] Embedding {len(filtered)} items...")
        embedder = EmbeddingEngine(config)
        embeddings = embedder.embed_contents(filtered)

        # 找到 filtered 内容对应的 db_id，将 embedding 写入 pgvector
        filtered_hashes = {rc.content_id for rc in filtered}
        db_contents = (
            db.query(DBContent)
            .filter(DBContent.job_id == job_id, DBContent.content_hash.in_(filtered_hashes))
            .all()
        )
        hash_to_dbid = {c.content_hash: c.id for c in db_contents}

        content_ids_for_vec = []
        embeddings_for_vec = []
        for i, rc in enumerate(filtered):
            dbid = hash_to_dbid.get(rc.content_id)
            if dbid is not None:
                content_ids_for_vec.append(dbid)
                embeddings_for_vec.append(embeddings[i])

        if content_ids_for_vec:
            import numpy as np
            vector_store.store_embeddings_batch(
                content_ids_for_vec, np.array(embeddings_for_vec)
            )
            logger.info(f"[Job {job_id}] {len(content_ids_for_vec)} embeddings stored in Supabase")

        # ── 4. 语义去重 ──
        logger.info(f"[Job {job_id}] Deduplicating...")
        dedup_cfg = config.get("pipeline", {}).get("dedup", {})
        deduper = Deduplicator(
            similarity_threshold=dedup_cfg.get("similarity_threshold", 0.88)
        )
        deduped, deduped_emb = deduper.deduplicate(filtered, embeddings)
        job.total_deduped = len(deduped)

        # 标记重复内容
        deduped_hashes = {rc.content_id for rc in deduped}
        for rc in filtered:
            if rc.content_id not in deduped_hashes:
                dbid = hash_to_dbid.get(rc.content_id)
                if dbid:
                    db.query(DBContent).filter(DBContent.id == dbid).update(
                        {"is_duplicate": True}
                    )
        db.commit()

        # ── 5. 话题聚类 ──
        logger.info(f"[Job {job_id}] Clustering...")
        clusterer = TopicClusterer(config)
        clusters = clusterer.cluster(deduped, deduped_emb)
        job.total_clusters = len(clusters)
        db.commit()

        # 保存聚类结果
        cluster_id_map = {}
        for cluster in clusters[:max_topics]:
            db_cluster = DBTopicCluster(
                job_id=job_id,
                cluster_index=cluster.cluster_id,
                size=cluster.size,
                total_engagement=cluster.total_engagement,
                avg_engagement=cluster.avg_engagement,
                sources=cluster.sources,
                top_titles=cluster.top_titles,
                representative_title=(
                    cluster.representative_content.title
                    if cluster.representative_content else ""
                ),
                representative_body=(
                    cluster.representative_content.body[:1000]
                    if cluster.representative_content else ""
                ),
            )
            db.add(db_cluster)
            db.flush()
            cluster_id_map[cluster.cluster_id] = db_cluster.id

            # 关联 contents → cluster
            for rc in cluster.contents:
                dbid = hash_to_dbid.get(rc.content_id)
                if dbid:
                    db.query(DBContent).filter(DBContent.id == dbid).update(
                        {"cluster_id": db_cluster.id}
                    )

        db.commit()

        # ── 6. 内容生成 ──
        logger.info(f"[Job {job_id}] Generating content ideas...")
        generator = ContentGenerator(config)
        idea_count = 0

        for cluster in clusters[:max_topics]:
            label = generator.generate_topic_label(cluster)
            cluster.label = label

            db_cluster_id = cluster_id_map.get(cluster.cluster_id)
            if db_cluster_id:
                db.query(DBTopicCluster).filter(
                    DBTopicCluster.id == db_cluster_id
                ).update({"label": label})

            ideas = generator.generate_all_formats(cluster, audience)
            for idea in ideas:
                db.add(DBContentIdea(
                    job_id=job_id,
                    cluster_id=db_cluster_id or 0,
                    audience_id=audience_id,
                    format_type=idea.format_type,
                    topic_label=idea.topic_label,
                    generated_content=idea.generated_content,
                    source_urls=idea.source_urls,
                ))
                idea_count += 1

        db.commit()

        job.total_ideas = idea_count
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        logger.info(f"[Job {job_id}] Completed! {idea_count} ideas generated.")

    except Exception as e:
        logger.exception(f"[Job {job_id}] Failed: {e}")
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()


def _scrape_all(config: dict, keywords: list[str]) -> list[RawContent]:
    all_content: list[RawContent] = []
    scrapers = [
        YouTubeScraper(config),
        RedditScraper(config),
        RSSScraper(config),
        GoogleTrendsScraper(config),
    ]
    for scraper in scrapers:
        try:
            results = scraper.scrape(keywords)
            all_content.extend(results)
        except Exception as e:
            logger.error(f"Scraper {scraper.source_name} failed: {e}")
    return all_content


def _raw_to_db(rc: RawContent, job_id: int) -> DBContent:
    return DBContent(
        job_id=job_id,
        content_hash=rc.content_id,
        source=rc.source,
        content_type=rc.content_type,
        title=rc.title,
        body=rc.body[:5000],
        url=rc.url,
        author=rc.author,
        published_at=rc.published_at,
        views=rc.views,
        likes=rc.likes,
        comments_count=rc.comments,
        engagement_score=rc.engagement_score,
        tags=rc.tags,
        extra=rc.extra,
        keyword_hits=rc.extra.get("keyword_hits", 0),
    )
