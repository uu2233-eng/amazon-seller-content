"""
RSS / Blog 抓取器

从 Amazon Seller 相关的知名博客 RSS 源获取最新文章。
使用 feedparser 库，无需 API Key。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from time import mktime

from .base import BaseScraper, RawContent

logger = logging.getLogger(__name__)


class RSSScraper(BaseScraper):
    source_name = "rss"

    def __init__(self, config: dict):
        super().__init__(config)
        self.rss_config = config.get("scraping", {}).get("rss", {})
        self.feeds = self.rss_config.get("feeds", [])
        self.lookback_days = config.get("scraping", {}).get("lookback_days", 7)

    def _parse_date(self, entry) -> datetime | None:
        for attr in ("published_parsed", "updated_parsed"):
            parsed = getattr(entry, attr, None)
            if parsed:
                try:
                    return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
                except (ValueError, OverflowError):
                    pass
        return None

    def _strip_html(self, html: str) -> str:
        from bs4 import BeautifulSoup
        return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)

    def scrape(self, keywords: list[str]) -> list[RawContent]:
        if not self.rss_config.get("enabled", True):
            logger.info("RSS scraper disabled in config.")
            return []

        import feedparser

        results: list[RawContent] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.lookback_days)

        for feed_info in self.feeds:
            feed_name = feed_info.get("name", "Unknown")
            feed_url = feed_info.get("url", "")
            if not feed_url:
                continue

            try:
                feed = feedparser.parse(feed_url)
                count = 0

                for entry in feed.entries:
                    pub_date = self._parse_date(entry)
                    if pub_date and pub_date < cutoff:
                        continue

                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    content = ""
                    if hasattr(entry, "content") and entry.content:
                        content = entry.content[0].get("value", "")

                    body_raw = content or summary
                    body = self._strip_html(body_raw)

                    tags = [t.get("term", "") for t in entry.get("tags", [])]

                    results.append(RawContent(
                        source="rss",
                        content_type="article",
                        title=title,
                        body=body,
                        url=entry.get("link", ""),
                        author=entry.get("author", feed_name),
                        published_at=pub_date,
                        tags=tags,
                        extra={"feed_name": feed_name, "feed_url": feed_url},
                    ))
                    count += 1

                logger.info(f"RSS: {feed_name} → {count} articles")

            except Exception as e:
                logger.error(f"RSS scrape error for {feed_name}: {e}")

        logger.info(f"RSS total: {len(results)} articles scraped.")
        return results
