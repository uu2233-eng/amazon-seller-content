"""
Amazon Seller Content Engine - 主流程

完整数据管道：
  Audience → Keyword → Raw Content → Filtered Content → Embedding → Topic Cluster → Content Ideas

使用方式：
  python -m src.main --audience fba_beginner
  python -m src.main --audience all
  python -m src.main --audience fba_beginner --formats article,short_video
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audiences import AUDIENCES, Audience, get_all_keywords, get_all_subreddits
from src.scrapers import YouTubeScraper, RedditScraper, RSSScraper, GoogleTrendsScraper
from src.scrapers.base import RawContent
from src.pipeline import KeywordFilter, EmbeddingEngine, Deduplicator, TopicClusterer
from src.generator import ContentGenerator
from src.utils.helpers import load_config, setup_logging

logger = logging.getLogger(__name__)
console = Console()


def run_scraping(config: dict, keywords: list[str]) -> list[RawContent]:
    """第一阶段：多源数据抓取"""
    all_content: list[RawContent] = []

    scrapers = [
        YouTubeScraper(config),
        RedditScraper(config),
        RSSScraper(config),
        GoogleTrendsScraper(config),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for scraper in scrapers:
            task = progress.add_task(f"Scraping {scraper.source_name}...", total=None)
            try:
                results = scraper.scrape(keywords)
                all_content.extend(results)
                progress.update(task, description=f"[green]✓ {scraper.source_name}: {len(results)} items")
            except Exception as e:
                progress.update(task, description=f"[red]✗ {scraper.source_name}: {e}")
                logger.error(f"Scraper {scraper.source_name} failed: {e}")

    return all_content


def run_pipeline(
    config: dict,
    raw_content: list[RawContent],
    keywords: list[str],
):
    """第二阶段：关键词过滤 → 向量化 → 去重 → 聚类"""

    # ① 关键词粗筛
    console.print("\n[bold]① Keyword Filtering...[/bold]")
    filter_config = config.get("pipeline", {}).get("keyword_filter", {})
    kw_filter = KeywordFilter(
        keywords=keywords,
        min_hits=filter_config.get("min_keyword_hits", 1),
        case_sensitive=filter_config.get("case_sensitive", False),
    )
    filtered = kw_filter.filter(raw_content)
    console.print(f"   {len(raw_content)} → {len(filtered)} (after keyword filter)")

    if not filtered:
        console.print("[yellow]No content passed keyword filter. Try broader keywords.[/yellow]")
        return [], []

    # ② 向量化
    console.print("\n[bold]② Generating Embeddings...[/bold]")
    embedder = EmbeddingEngine(config)
    embeddings = embedder.embed_contents(filtered)
    console.print(f"   Embedded {len(filtered)} items → shape {embeddings.shape}")

    # ② (续) 语义去重
    console.print("\n[bold]② Semantic Deduplication...[/bold]")
    dedup_config = config.get("pipeline", {}).get("dedup", {})
    deduper = Deduplicator(
        similarity_threshold=dedup_config.get("similarity_threshold", 0.88)
    )
    deduped_content, deduped_embeddings = deduper.deduplicate(filtered, embeddings)
    console.print(f"   {len(filtered)} → {len(deduped_content)} (after dedup)")

    # ③ 话题聚类
    console.print("\n[bold]③ Topic Clustering...[/bold]")
    clusterer = TopicClusterer(config)
    clusters = clusterer.cluster(deduped_content, deduped_embeddings)
    console.print(f"   Found {len(clusters)} topic clusters")

    return clusters, deduped_content


def display_clusters(clusters):
    """展示话题簇概览"""
    table = Table(title="Topic Clusters Overview")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Label", style="bold")
    table.add_column("Size", justify="right")
    table.add_column("Sources", style="green")
    table.add_column("Engagement", justify="right", style="yellow")
    table.add_column("Top Title")

    for c in clusters:
        table.add_row(
            str(c.cluster_id),
            c.label or "—",
            str(c.size),
            ", ".join(c.sources),
            f"{c.total_engagement:.0f}",
            (c.top_titles[0][:60] + "...") if c.top_titles else "—",
        )

    console.print(table)


def run_generation(
    config: dict,
    clusters,
    audience: Audience,
):
    """第三阶段：内容创意生成"""
    generator = ContentGenerator(config)
    output_config = config.get("output", {})
    max_topics = output_config.get("max_topics", 20)

    console.print(f"\n[bold]Generating content for top {min(max_topics, len(clusters))} topics...[/bold]")

    # 先给每个簇打标签
    for cluster in clusters[:max_topics]:
        if not cluster.label:
            cluster.label = generator.generate_topic_label(cluster)
            console.print(f"  Cluster #{cluster.cluster_id}: [cyan]{cluster.label}[/cyan]")

    display_clusters(clusters[:max_topics])

    # 生成全部内容
    ideas = generator.batch_generate(clusters, audience, max_topics)

    # 导出
    output_dir = output_config.get("dir", "output")
    output_format = output_config.get("format", "markdown")
    generator.export_ideas(ideas, output_dir, output_format)

    console.print(f"\n[green bold]✓ Generated {len(ideas)} content ideas![/green bold]")
    console.print(f"  Output directory: {os.path.abspath(output_dir)}")

    return ideas


def main():
    parser = argparse.ArgumentParser(
        description="Amazon Seller Content Engine - 热点内容抓取与创意生成"
    )
    parser.add_argument(
        "--audience", "-a",
        default="fba_beginner",
        help=f"Target audience ID. Available: {', '.join(AUDIENCES.keys())}, all",
    )
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--formats", "-f",
        default=None,
        help="Comma-separated output formats (article,short_video,long_video,image_prompt,social_post)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only scrape and cluster, skip content generation",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)
    config = load_config(args.config)

    if args.formats:
        config.setdefault("generation", {})["output_formats"] = args.formats.split(",")

    console.print("[bold blue]═══ Amazon Seller Content Engine ═══[/bold blue]\n")

    # 选择受众
    if args.audience == "all":
        audiences_to_process = list(AUDIENCES.values())
    else:
        if args.audience not in AUDIENCES:
            console.print(f"[red]Unknown audience: {args.audience}[/red]")
            console.print(f"Available: {', '.join(AUDIENCES.keys())}")
            sys.exit(1)
        audiences_to_process = [AUDIENCES[args.audience]]

    for audience in audiences_to_process:
        console.print(f"\n[bold magenta]▶ Audience: {audience.name}[/bold magenta]")
        console.print(f"  {audience.description}")
        console.print(f"  Keywords: {len(audience.all_keywords)}")

        # ① 抓取
        keywords = audience.all_keywords
        raw_content = run_scraping(config, keywords)
        console.print(f"\n  [bold]Total raw content: {len(raw_content)}[/bold]")

        if not raw_content:
            console.print("[yellow]  No content found. Check API keys and network.[/yellow]")
            continue

        # ② 管道处理
        clusters, deduped = run_pipeline(config, raw_content, keywords)

        if not clusters:
            console.print("[yellow]  No clusters formed. Try different parameters.[/yellow]")
            continue

        if args.dry_run:
            display_clusters(clusters)
            console.print("[yellow]  Dry run - skipping content generation.[/yellow]")
            continue

        # ③ 生成内容
        run_generation(config, clusters, audience)

    console.print("\n[bold green]═══ Done! ═══[/bold green]")


if __name__ == "__main__":
    main()
