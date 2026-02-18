-- ============================================================
-- 迁移: OpenAI embedding (1536维) → Gemini embedding (768维)
-- 在 Supabase Dashboard → SQL Editor 中运行此文件
-- ============================================================

-- 1. 修改 contents 表的 embedding 列维度
ALTER TABLE contents DROP COLUMN IF EXISTS embedding;
ALTER TABLE contents ADD COLUMN embedding vector(768);

-- 2. 重建语义搜索函数
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
