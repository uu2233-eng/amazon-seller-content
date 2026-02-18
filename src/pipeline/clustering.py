"""
话题聚类模块

Pipeline 第 ③ 步：将去重后的内容聚合成话题簇。
每个簇代表一个热点话题方向，可直接用于内容创意生成。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

from src.scrapers.base import RawContent

logger = logging.getLogger(__name__)


@dataclass
class TopicCluster:
    """一个话题簇"""
    cluster_id: int
    label: str = ""                                    # 由 LLM 生成的话题标签
    contents: list[RawContent] = field(default_factory=list)
    centroid: np.ndarray | None = None
    representative_content: RawContent | None = None   # 离质心最近的内容

    @property
    def size(self) -> int:
        return len(self.contents)

    @property
    def total_engagement(self) -> float:
        return sum(c.engagement_score for c in self.contents)

    @property
    def avg_engagement(self) -> float:
        if not self.contents:
            return 0
        return self.total_engagement / len(self.contents)

    @property
    def sources(self) -> list[str]:
        return list({c.source for c in self.contents})

    @property
    def top_titles(self) -> list[str]:
        sorted_c = sorted(self.contents, key=lambda c: c.engagement_score, reverse=True)
        return [c.title for c in sorted_c[:5]]

    def summary_text(self) -> str:
        """生成用于 LLM 输入的摘要文本"""
        lines = [f"Topic Cluster #{self.cluster_id}"]
        lines.append(f"Size: {self.size} items | Sources: {', '.join(self.sources)}")
        lines.append(f"Total Engagement: {self.total_engagement:.0f}")
        lines.append("Top content titles:")
        for i, title in enumerate(self.top_titles, 1):
            lines.append(f"  {i}. {title}")
        if self.representative_content:
            lines.append(f"\nRepresentative content:")
            lines.append(f"  Title: {self.representative_content.title}")
            body_preview = self.representative_content.body[:300]
            lines.append(f"  Body: {body_preview}...")
        return "\n".join(lines)


class TopicClusterer:

    def __init__(self, config: dict):
        cluster_config = config.get("pipeline", {}).get("clustering", {})
        self.algorithm = cluster_config.get("algorithm", "hdbscan")
        self.min_cluster_size = cluster_config.get("min_cluster_size", 3)
        self.min_samples = cluster_config.get("min_samples", 2)
        self.n_clusters = cluster_config.get("kmeans_n_clusters", 10)

    def cluster(
        self,
        contents: list[RawContent],
        embeddings: np.ndarray,
    ) -> list[TopicCluster]:
        if len(contents) < 2:
            if contents:
                return [self._make_cluster(0, contents, embeddings)]
            return []

        if self.algorithm == "hdbscan":
            labels = self._cluster_hdbscan(embeddings)
        else:
            labels = self._cluster_kmeans(embeddings)

        return self._build_clusters(contents, embeddings, labels)

    def _cluster_hdbscan(self, embeddings: np.ndarray) -> np.ndarray:
        try:
            import hdbscan
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                metric="euclidean",
            )
            labels = clusterer.fit_predict(embeddings)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = (labels == -1).sum()
            logger.info(
                f"HDBSCAN: {n_clusters} clusters, {n_noise} noise points"
            )
            return labels
        except ImportError:
            logger.warning("hdbscan not installed, falling back to KMeans")
            return self._cluster_kmeans(embeddings)

    def _cluster_kmeans(self, embeddings: np.ndarray) -> np.ndarray:
        from sklearn.cluster import KMeans

        k = min(self.n_clusters, len(embeddings))
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        logger.info(f"KMeans: {k} clusters")
        return labels

    def _build_clusters(
        self,
        contents: list[RawContent],
        embeddings: np.ndarray,
        labels: np.ndarray,
    ) -> list[TopicCluster]:
        clusters: dict[int, TopicCluster] = {}

        for idx, label in enumerate(labels):
            label = int(label)
            if label == -1:
                continue  # 噪声点（HDBSCAN）

            if label not in clusters:
                clusters[label] = TopicCluster(cluster_id=label)
            clusters[label].contents.append(contents[idx])

        result = []
        for label, cluster in clusters.items():
            mask = labels == label
            cluster_embeddings = embeddings[mask]
            centroid = cluster_embeddings.mean(axis=0)
            cluster.centroid = centroid

            # 找离质心最近的内容作为代表
            from sklearn.metrics.pairwise import cosine_similarity
            sims = cosine_similarity([centroid], cluster_embeddings)[0]
            rep_idx = int(np.argmax(sims))
            cluster.representative_content = cluster.contents[rep_idx]

            result.append(cluster)

        result.sort(key=lambda c: c.total_engagement, reverse=True)

        logger.info(
            f"Built {len(result)} topic clusters "
            f"(sizes: {[c.size for c in result]})"
        )
        return result

    def _make_cluster(
        self,
        cluster_id: int,
        contents: list[RawContent],
        embeddings: np.ndarray,
    ) -> TopicCluster:
        cluster = TopicCluster(cluster_id=cluster_id, contents=contents)
        if len(embeddings) > 0:
            cluster.centroid = embeddings.mean(axis=0)
            cluster.representative_content = contents[0]
        return cluster
