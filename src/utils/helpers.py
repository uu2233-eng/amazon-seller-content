"""
工具函数
"""

from __future__ import annotations

import logging
import os
import sys

import yaml


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件，并用环境变量覆盖 API key"""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # .env 文件支持
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_keys = config.setdefault("api_keys", {})
    env_map = {
        "OPENAI_API_KEY": "openai_api_key",
        "YOUTUBE_API_KEY": "youtube_api_key",
        "REDDIT_CLIENT_ID": "reddit_client_id",
        "REDDIT_CLIENT_SECRET": "reddit_client_secret",
    }
    for env_var, config_key in env_map.items():
        val = os.getenv(env_var, "")
        if val:
            api_keys[config_key] = val

    return config


def setup_logging(level: str = "INFO"):
    """配置日志格式"""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )


def truncate_text(text: str, max_length: int = 500) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
