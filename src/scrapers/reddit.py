"""
Reddit 抓取器 (PRAW)

从指定的 subreddit 中抓取近一周的热门/新帖子。
Reddit API 免费使用，需要创建一个 Reddit App 获取 client_id 和 client_secret。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from .base import BaseScraper, RawContent

logger = logging.getLogger(__name__)


class RedditScraper(BaseScraper):
    source_name = "reddit"

    def __init__(self, config: dict):
        super().__init__(config)
        self.reddit_config = config.get("scraping", {}).get("reddit", {})
        api_keys = config.get("api_keys", {})
        self.client_id = api_keys.get("reddit_client_id", "")
        self.client_secret = api_keys.get("reddit_client_secret", "")
        self.user_agent = api_keys.get(
            "reddit_user_agent", "AmazonSellerContentEngine/1.0"
        )
        self.subreddits = self.reddit_config.get("subreddits", [])
        self.sort = self.reddit_config.get("sort", "hot")
        self.time_filter = self.reddit_config.get("time_filter", "week")
        self.lookback_days = config.get("scraping", {}).get("lookback_days", 7)
        self.max_results = config.get("scraping", {}).get("max_results_per_source", 100)

    def _build_client(self):
        import praw
        return praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
        )

    def _is_recent(self, created_utc: float) -> bool:
        post_time = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.lookback_days)
        return post_time >= cutoff

    def scrape(self, keywords: list[str]) -> list[RawContent]:
        if not self.client_id or not self.client_secret:
            logger.warning("Reddit API credentials not configured, skipping.")
            return []

        if not self.reddit_config.get("enabled", True):
            logger.info("Reddit scraper disabled in config.")
            return []

        reddit = self._build_client()
        results: list[RawContent] = []
        seen_ids: set[str] = set()
        keyword_set = {kw.lower() for kw in keywords}

        for sub_name in self.subreddits:
            try:
                subreddit = reddit.subreddit(sub_name)

                if self.sort == "hot":
                    posts = subreddit.hot(limit=self.max_results)
                elif self.sort == "new":
                    posts = subreddit.new(limit=self.max_results)
                elif self.sort == "top":
                    posts = subreddit.top(
                        time_filter=self.time_filter, limit=self.max_results
                    )
                else:
                    posts = subreddit.hot(limit=self.max_results)

                count = 0
                for post in posts:
                    if post.id in seen_ids:
                        continue
                    if not self._is_recent(post.created_utc):
                        continue

                    title_lower = post.title.lower()
                    body_lower = (post.selftext or "").lower()
                    combined = f"{title_lower} {body_lower}"

                    hit = any(kw in combined for kw in keyword_set)
                    if not hit:
                        continue

                    seen_ids.add(post.id)
                    published_at = datetime.fromtimestamp(
                        post.created_utc, tz=timezone.utc
                    )

                    results.append(RawContent(
                        source="reddit",
                        content_type="post",
                        title=post.title,
                        body=post.selftext or "",
                        url=f"https://reddit.com{post.permalink}",
                        author=str(post.author) if post.author else "[deleted]",
                        published_at=published_at,
                        views=0,
                        likes=post.score,
                        comments=post.num_comments,
                        tags=[sub_name],
                        extra={
                            "subreddit": sub_name,
                            "upvote_ratio": post.upvote_ratio,
                            "is_self": post.is_self,
                        },
                    ))
                    count += 1

                logger.info(f"Reddit: r/{sub_name} → {count} posts matched")

            except Exception as e:
                logger.error(f"Reddit scrape error for r/{sub_name}: {e}")

        logger.info(f"Reddit total: {len(results)} posts scraped.")
        return results
