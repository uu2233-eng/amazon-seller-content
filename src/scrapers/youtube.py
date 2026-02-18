"""
YouTube Data API v3 抓取器

通过关键词搜索近一周的 YouTube 视频，获取标题、描述、互动数据。
API 免费配额: 10,000 units/day, 每次 search.list = 100 units。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from .base import BaseScraper, RawContent

logger = logging.getLogger(__name__)


class YouTubeScraper(BaseScraper):
    source_name = "youtube"

    def __init__(self, config: dict):
        super().__init__(config)
        self.yt_config = config.get("scraping", {}).get("youtube", {})
        self.api_key = (
            config.get("api_keys", {}).get("youtube_api_key", "")
        )
        self.max_results = self.yt_config.get("max_results", 50)
        self.region_code = self.yt_config.get("region_code", "US")
        self.lookback_days = config.get("scraping", {}).get("lookback_days", 7)

    def _build_service(self):
        from googleapiclient.discovery import build
        return build("youtube", "v3", developerKey=self.api_key)

    def scrape(self, keywords: list[str]) -> list[RawContent]:
        if not self.api_key:
            logger.warning("YouTube API key not configured, skipping.")
            return []

        if not self.yt_config.get("enabled", True):
            logger.info("YouTube scraper disabled in config.")
            return []

        service = self._build_service()
        results: list[RawContent] = []
        seen_ids: set[str] = set()
        published_after = (
            datetime.now(timezone.utc) - timedelta(days=self.lookback_days)
        ).isoformat()

        for keyword in keywords:
            try:
                response = service.search().list(
                    q=keyword,
                    part="snippet",
                    type="video",
                    maxResults=min(self.max_results, 50),
                    order=self.yt_config.get("order", "relevance"),
                    regionCode=self.region_code,
                    relevanceLanguage=self.yt_config.get("relevance_language", "en"),
                    publishedAfter=published_after,
                ).execute()

                video_ids = []
                snippets = {}
                for item in response.get("items", []):
                    vid = item["id"]["videoId"]
                    if vid not in seen_ids:
                        seen_ids.add(vid)
                        video_ids.append(vid)
                        snippets[vid] = item["snippet"]

                if not video_ids:
                    continue

                stats_response = service.videos().list(
                    part="statistics",
                    id=",".join(video_ids),
                ).execute()

                stats_map = {}
                for item in stats_response.get("items", []):
                    stats_map[item["id"]] = item.get("statistics", {})

                for vid in video_ids:
                    snippet = snippets[vid]
                    stats = stats_map.get(vid, {})
                    pub_str = snippet.get("publishedAt", "")
                    published_at = None
                    if pub_str:
                        try:
                            published_at = datetime.fromisoformat(
                                pub_str.replace("Z", "+00:00")
                            )
                        except ValueError:
                            pass

                    results.append(RawContent(
                        source="youtube",
                        content_type="video",
                        title=snippet.get("title", ""),
                        body=snippet.get("description", ""),
                        url=f"https://www.youtube.com/watch?v={vid}",
                        author=snippet.get("channelTitle", ""),
                        published_at=published_at,
                        views=int(stats.get("viewCount", 0)),
                        likes=int(stats.get("likeCount", 0)),
                        comments=int(stats.get("commentCount", 0)),
                        tags=snippet.get("tags", []) if "tags" in snippet else [],
                        thumbnail_url=snippet.get("thumbnails", {}).get(
                            "high", {}
                        ).get("url", ""),
                        extra={"keyword_query": keyword},
                    ))

                logger.info(
                    f"YouTube: keyword='{keyword}' → {len(video_ids)} videos"
                )

            except Exception as e:
                logger.error(f"YouTube scrape error for '{keyword}': {e}")

        logger.info(f"YouTube total: {len(results)} videos scraped.")
        return results
