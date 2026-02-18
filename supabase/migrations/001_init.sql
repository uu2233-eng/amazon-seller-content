-- ============================================================
-- Amazon Seller Content Engine — Supabase 初始化迁移
-- 在 Supabase Dashboard → SQL Editor 中运行此文件
-- ============================================================

-- 启用 pgvector 扩展（向量存储）
CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────────
-- 1. audiences (受众)
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audiences (
    id          VARCHAR(64) PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    core_keywords     JSONB DEFAULT '[]'::jsonb,
    extended_keywords JSONB DEFAULT '[]'::jsonb,
    subreddits        JSONB DEFAULT '[]'::jsonb,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────────────
-- 2. scrape_jobs (抓取任务)
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id              SERIAL PRIMARY KEY,
    audience_id     VARCHAR(64) NOT NULL REFERENCES audiences(id),
    status          VARCHAR(20) DEFAULT 'pending',
    sources_config  JSONB DEFAULT '{}'::jsonb,
    total_raw       INTEGER DEFAULT 0,
    total_filtered  INTEGER DEFAULT 0,
    total_deduped   INTEGER DEFAULT 0,
    total_clusters  INTEGER DEFAULT 0,
    total_ideas     INTEGER DEFAULT 0,
    error_message   TEXT DEFAULT '',
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON scrape_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_audience ON scrape_jobs(audience_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON scrape_jobs(created_at DESC);

-- ─────────────────────────────────────────────────
-- 3. topic_clusters (话题簇) — 需要先于 contents 建表
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS topic_clusters (
    id                   SERIAL PRIMARY KEY,
    job_id               INTEGER NOT NULL REFERENCES scrape_jobs(id) ON DELETE CASCADE,
    cluster_index        INTEGER,
    label                VARCHAR(300) DEFAULT '',
    size                 INTEGER DEFAULT 0,
    total_engagement     DOUBLE PRECISION DEFAULT 0,
    avg_engagement       DOUBLE PRECISION DEFAULT 0,
    sources              JSONB DEFAULT '[]'::jsonb,
    top_titles           JSONB DEFAULT '[]'::jsonb,
    representative_title VARCHAR(500) DEFAULT '',
    representative_body  TEXT DEFAULT '',
    created_at           TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clusters_job ON topic_clusters(job_id);
CREATE INDEX IF NOT EXISTS idx_clusters_engagement ON topic_clusters(total_engagement DESC);

-- ─────────────────────────────────────────────────
-- 4. contents (内容 + embedding 向量)
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contents (
    id               SERIAL PRIMARY KEY,
    job_id           INTEGER NOT NULL REFERENCES scrape_jobs(id) ON DELETE CASCADE,
    content_hash     VARCHAR(32),
    source           VARCHAR(30) NOT NULL,
    content_type     VARCHAR(30),
    title            VARCHAR(500),
    body             TEXT DEFAULT '',
    url              VARCHAR(1000),
    author           VARCHAR(200) DEFAULT '',
    published_at     TIMESTAMP,
    views            INTEGER DEFAULT 0,
    likes            INTEGER DEFAULT 0,
    comments_count   INTEGER DEFAULT 0,
    engagement_score DOUBLE PRECISION DEFAULT 0,
    tags             JSONB DEFAULT '[]'::jsonb,
    extra            JSONB DEFAULT '{}'::jsonb,
    keyword_hits     INTEGER DEFAULT 0,
    is_duplicate     BOOLEAN DEFAULT FALSE,
    cluster_id       INTEGER REFERENCES topic_clusters(id),
    embedding        vector(768),              -- pgvector: Gemini text-embedding-004
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contents_job ON contents(job_id);
CREATE INDEX IF NOT EXISTS idx_contents_hash ON contents(content_hash);
CREATE INDEX IF NOT EXISTS idx_contents_source ON contents(source);
CREATE INDEX IF NOT EXISTS idx_contents_cluster ON contents(cluster_id);
CREATE INDEX IF NOT EXISTS idx_contents_duplicate ON contents(is_duplicate) WHERE is_duplicate = FALSE;

-- ─────────────────────────────────────────────────
-- 5. content_ideas (内容创意)
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS content_ideas (
    id                SERIAL PRIMARY KEY,
    job_id            INTEGER NOT NULL REFERENCES scrape_jobs(id) ON DELETE CASCADE,
    cluster_id        INTEGER NOT NULL REFERENCES topic_clusters(id) ON DELETE CASCADE,
    audience_id       VARCHAR(64),
    format_type       VARCHAR(30),
    topic_label       VARCHAR(300),
    generated_content TEXT DEFAULT '',
    source_urls       JSONB DEFAULT '[]'::jsonb,
    is_favorite       BOOLEAN DEFAULT FALSE,
    is_published      BOOLEAN DEFAULT FALSE,
    notes             TEXT DEFAULT '',
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ideas_job ON content_ideas(job_id);
CREATE INDEX IF NOT EXISTS idx_ideas_cluster ON content_ideas(cluster_id);
CREATE INDEX IF NOT EXISTS idx_ideas_audience ON content_ideas(audience_id);
CREATE INDEX IF NOT EXISTS idx_ideas_format ON content_ideas(format_type);
CREATE INDEX IF NOT EXISTS idx_ideas_favorite ON content_ideas(is_favorite) WHERE is_favorite = TRUE;
CREATE INDEX IF NOT EXISTS idx_ideas_created ON content_ideas(created_at DESC);

-- ─────────────────────────────────────────────────
-- 6. 向量索引 (IVFFlat) — 数据量 > 1000 后建议启用
-- ─────────────────────────────────────────────────
-- 取消注释下面这行以创建向量索引（加速语义搜索）：
-- CREATE INDEX idx_contents_embedding ON contents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ─────────────────────────────────────────────────
-- 7. 语义搜索函数 (可选，Supabase Edge Function 可直接调用)
-- ─────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION match_contents(
    query_embedding vector(768),
    match_threshold FLOAT DEFAULT 0.75,
    match_count INT DEFAULT 10,
    filter_job_id INT DEFAULT NULL
)
RETURNS TABLE (
    id               INT,
    title            VARCHAR(500),
    url              VARCHAR(1000),
    source           VARCHAR(30),
    engagement_score DOUBLE PRECISION,
    similarity       DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.title,
        c.url,
        c.source,
        c.engagement_score,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM contents c
    WHERE c.embedding IS NOT NULL
      AND 1 - (c.embedding <=> query_embedding) >= match_threshold
      AND (filter_job_id IS NULL OR c.job_id = filter_job_id)
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- ─────────────────────────────────────────────────
-- 8. RLS (Row Level Security) — 按需启用
-- ─────────────────────────────────────────────────
-- 如果需要多用户隔离，取消注释以下内容：
-- ALTER TABLE audiences ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE scrape_jobs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE contents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE topic_clusters ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE content_ideas ENABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────────
-- 9. updated_at 自动更新触发器
-- ─────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_audiences_updated
    BEFORE UPDATE ON audiences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER trg_ideas_updated
    BEFORE UPDATE ON content_ideas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
