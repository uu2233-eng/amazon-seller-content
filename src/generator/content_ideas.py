"""
内容创意生成器

将话题簇（TopicCluster）+ 受众定义（Audience）→ 完整的内容创意。
通过 LLM 生成：文案、图片 Prompt、视频脚本、社交帖子等。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

from src.audiences import Audience
from src.pipeline.clustering import TopicCluster
from .templates import PromptTemplates

logger = logging.getLogger(__name__)


@dataclass
class ContentIdea:
    """一条完整的内容创意"""
    topic_cluster_id: int
    topic_label: str
    audience_id: str
    format_type: str            # article / short_video / long_video / image_prompt / social_post
    generated_content: str      # LLM 生成的完整内容
    source_urls: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_markdown(self) -> str:
        lines = [
            f"# {self.topic_label}",
            f"",
            f"**Format**: {self.format_type}",
            f"**Audience**: {self.audience_id}",
            f"**Generated**: {self.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            f"",
            "---",
            f"",
            self.generated_content,
            f"",
            "---",
            f"",
            "## Source References",
        ]
        for url in self.source_urls[:10]:
            lines.append(f"- {url}")
        return "\n".join(lines)


class ContentGenerator:

    def __init__(self, config: dict):
        gen_config = config.get("generation", {})
        self.model = gen_config.get("model", "gpt-4o")
        self.temperature = gen_config.get("temperature", 0.8)
        self.max_tokens = gen_config.get("max_tokens", 4000)
        self.output_formats = gen_config.get("output_formats", ["article"])
        self.api_key = config.get("api_keys", {}).get("openai_api_key", "")

    def _call_llm(self, prompt: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a world-class content creator specializing in Amazon seller education and e-commerce content."},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content or ""

    def generate_topic_label(self, cluster: TopicCluster) -> str:
        """用 LLM 为话题簇生成标签"""
        if not self.api_key:
            titles = cluster.top_titles
            return titles[0] if titles else f"Topic #{cluster.cluster_id}"

        prompt = PromptTemplates.TOPIC_LABEL.format(
            titles="\n".join(f"- {t}" for t in cluster.top_titles),
            body=(
                cluster.representative_content.body[:500]
                if cluster.representative_content
                else ""
            ),
        )

        try:
            label = self._call_llm(prompt).strip().strip('"').strip("'")
            return label
        except Exception as e:
            logger.error(f"Failed to generate topic label: {e}")
            return cluster.top_titles[0] if cluster.top_titles else f"Topic #{cluster.cluster_id}"

    def generate_content(
        self,
        cluster: TopicCluster,
        audience: Audience,
        format_type: str,
    ) -> ContentIdea:
        """为一个话题簇生成指定格式的内容创意"""
        template = PromptTemplates.get_template(format_type)
        prompt = template.format(
            topic_summary=cluster.summary_text(),
            audience_description=f"{audience.name}: {audience.description}",
        )

        logger.info(
            f"Generating {format_type} for cluster #{cluster.cluster_id} "
            f"(audience: {audience.id})"
        )

        try:
            content = self._call_llm(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            content = f"[Generation failed: {e}]"

        source_urls = [c.url for c in cluster.contents[:10]]

        return ContentIdea(
            topic_cluster_id=cluster.cluster_id,
            topic_label=cluster.label or f"Topic #{cluster.cluster_id}",
            audience_id=audience.id,
            format_type=format_type,
            generated_content=content,
            source_urls=source_urls,
        )

    def generate_all_formats(
        self,
        cluster: TopicCluster,
        audience: Audience,
    ) -> list[ContentIdea]:
        """为一个话题簇生成所有配置的内容格式"""
        ideas = []
        for fmt in self.output_formats:
            idea = self.generate_content(cluster, audience, fmt)
            ideas.append(idea)
        return ideas

    def batch_generate(
        self,
        clusters: list[TopicCluster],
        audience: Audience,
        max_topics: int = 20,
    ) -> list[ContentIdea]:
        """批量生成：为多个话题簇生成内容"""
        all_ideas = []

        for cluster in clusters[:max_topics]:
            if not cluster.label:
                cluster.label = self.generate_topic_label(cluster)
                logger.info(f"Cluster #{cluster.cluster_id} label: {cluster.label}")

            ideas = self.generate_all_formats(cluster, audience)
            all_ideas.extend(ideas)

        logger.info(f"Generated {len(all_ideas)} content ideas total.")
        return all_ideas

    def export_ideas(
        self,
        ideas: list[ContentIdea],
        output_dir: str,
        format: str = "markdown",
    ):
        """导出内容创意到文件"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if format in ("markdown", "both"):
            for i, idea in enumerate(ideas):
                filename = (
                    f"{timestamp}_{idea.audience_id}_{idea.format_type}"
                    f"_topic{idea.topic_cluster_id}_{i+1}.md"
                )
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(idea.to_markdown())
            logger.info(f"Exported {len(ideas)} markdown files to {output_dir}")

        if format in ("json", "both"):
            json_data = []
            for idea in ideas:
                json_data.append({
                    "topic_cluster_id": idea.topic_cluster_id,
                    "topic_label": idea.topic_label,
                    "audience_id": idea.audience_id,
                    "format_type": idea.format_type,
                    "generated_content": idea.generated_content,
                    "source_urls": idea.source_urls,
                    "generated_at": idea.generated_at.isoformat(),
                })
            filepath = os.path.join(output_dir, f"{timestamp}_all_ideas.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Exported JSON to {filepath}")
