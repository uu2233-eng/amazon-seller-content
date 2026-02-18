"""
Google Trends 抓取器

使用 pytrends 获取 Amazon Seller 相关关键词的搜索热度和相关查询。
这些数据用于发现新兴话题和验证话题热度。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from .base import BaseScraper, RawContent

logger = logging.getLogger(__name__)


class GoogleTrendsScraper(BaseScraper):
    source_name = "google_trends"

    def __init__(self, config: dict):
        super().__init__(config)
        self.trends_config = config.get("scraping", {}).get("google_trends", {})
        self.geo = self.trends_config.get("geo", "US")
        self.timeframe = self.trends_config.get("timeframe", "now 7-d")

    def scrape(self, keywords: list[str]) -> list[RawContent]:
        if not self.trends_config.get("enabled", True):
            logger.info("Google Trends scraper disabled in config.")
            return []

        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=360)
        results: list[RawContent] = []

        # pytrends 每次最多查询 5 个关键词
        batches = [keywords[i:i + 5] for i in range(0, len(keywords), 5)]

        for batch in batches:
            try:
                pytrends.build_payload(
                    batch,
                    cat=0,
                    timeframe=self.timeframe,
                    geo=self.geo,
                )

                # 获取相关查询
                related = pytrends.related_queries()
                for kw, data in related.items():
                    for query_type in ("top", "rising"):
                        df = data.get(query_type)
                        if df is None or df.empty:
                            continue

                        for _, row in df.iterrows():
                            query_text = row.get("query", "")
                            value = row.get("value", 0)

                            results.append(RawContent(
                                source="google_trends",
                                content_type="trend",
                                title=f"[Trending] {query_text}",
                                body=f"Related to '{kw}'. Type: {query_type}. Value: {value}",
                                url=f"https://trends.google.com/trends/explore?q={query_text.replace(' ', '+')}&geo={self.geo}",
                                published_at=datetime.now(timezone.utc),
                                views=int(value) if str(value).isdigit() else 0,
                                tags=[kw, query_type],
                                extra={
                                    "parent_keyword": kw,
                                    "trend_type": query_type,
                                    "trend_value": str(value),
                                },
                            ))

                # 获取相关话题
                related_topics = pytrends.related_topics()
                for kw, data in related_topics.items():
                    for topic_type in ("top", "rising"):
                        df = data.get(topic_type)
                        if df is None or df.empty:
                            continue

                        for _, row in df.iterrows():
                            topic_title = row.get("topic_title", "")
                            topic_type_val = row.get("topic_type", "")
                            value = row.get("value", 0)

                            results.append(RawContent(
                                source="google_trends",
                                content_type="trend",
                                title=f"[Topic] {topic_title} ({topic_type_val})",
                                body=f"Related topic for '{kw}'. Type: {topic_type}. Value: {value}",
                                url=f"https://trends.google.com/trends/explore?q={kw.replace(' ', '+')}&geo={self.geo}",
                                published_at=datetime.now(timezone.utc),
                                tags=[kw, topic_type, topic_type_val],
                                extra={
                                    "parent_keyword": kw,
                                    "topic_type": topic_type,
                                    "topic_title": topic_title,
                                },
                            ))

                logger.info(f"Google Trends: batch {batch} processed")

            except Exception as e:
                logger.error(f"Google Trends error for {batch}: {e}")

        logger.info(f"Google Trends total: {len(results)} trend items scraped.")
        return results
