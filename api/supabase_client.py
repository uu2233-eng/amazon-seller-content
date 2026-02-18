"""
Supabase Python Client 封装

提供两种连接方式：
  1. SQLAlchemy (database.py) — 用于 ORM 操作，主流程使用
  2. Supabase Client (本文件) — 用于 Supabase 特有功能：
     - Auth (用户认证)
     - Storage (文件存储，存生成的图片等)
     - Realtime (实时订阅任务状态)
     - Edge Functions
"""

from __future__ import annotations

import os
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_client = None


def get_supabase_client():
    """获取 Supabase Client 单例"""
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")

    if not url or not key:
        logger.info("Supabase URL/Key not configured, client not available")
        return None

    try:
        from supabase import create_client
        _client = create_client(url, key)
        logger.info(f"Supabase client connected to {url}")
        return _client
    except ImportError:
        logger.warning("supabase package not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None


def supabase_rpc(function_name: str, params: dict) -> dict | None:
    """
    调用 Supabase Database Function (RPC)

    例：调用 match_contents 做语义搜索
      supabase_rpc("match_contents", {
          "query_embedding": [...],
          "match_threshold": 0.75,
          "match_count": 10
      })
    """
    client = get_supabase_client()
    if not client:
        return None

    try:
        result = client.rpc(function_name, params).execute()
        return result.data
    except Exception as e:
        logger.error(f"Supabase RPC '{function_name}' failed: {e}")
        return None


def upload_to_storage(bucket: str, path: str, file_bytes: bytes, content_type: str = "text/markdown") -> str | None:
    """
    上传文件到 Supabase Storage

    用途：将生成的 Markdown 内容存到云端
    返回公共 URL
    """
    client = get_supabase_client()
    if not client:
        return None

    try:
        client.storage.from_(bucket).upload(
            path, file_bytes, {"content-type": content_type}
        )
        url = client.storage.from_(bucket).get_public_url(path)
        return url
    except Exception as e:
        logger.error(f"Storage upload failed: {e}")
        return None
