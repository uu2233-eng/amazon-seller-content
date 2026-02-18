"""
受众定义与关键词库

数据关系：Audience → Keywords → (用于抓取和过滤)
每个受众群体有独立的关键词集合，关键词分为核心词和扩展词两层。
"""

from dataclasses import dataclass, field


@dataclass
class Audience:
    id: str
    name: str
    description: str
    core_keywords: list[str] = field(default_factory=list)
    extended_keywords: list[str] = field(default_factory=list)
    subreddits: list[str] = field(default_factory=list)
    youtube_channels: list[str] = field(default_factory=list)
    rss_feeds: list[str] = field(default_factory=list)

    @property
    def all_keywords(self) -> list[str]:
        return self.core_keywords + self.extended_keywords

    def get_search_queries(self, max_queries: int = 10) -> list[str]:
        """生成用于搜索引擎/API 的查询组合"""
        queries = []
        for kw in self.core_keywords[:max_queries]:
            queries.append(kw)
        for kw in self.core_keywords[:3]:
            queries.append(f"{kw} 2026")
            queries.append(f"{kw} tips")
            queries.append(f"{kw} strategy")
        return queries[:max_queries]


# =============================================================
# 受众群体定义
# =============================================================

AUDIENCES: dict[str, Audience] = {}


def _register(audience: Audience):
    AUDIENCES[audience.id] = audience
    return audience


# --- 1. Amazon FBA 新手卖家 ---
_register(Audience(
    id="fba_beginner",
    name="Amazon FBA Beginners",
    description="刚入门或正在研究 Amazon FBA 的新手卖家",
    core_keywords=[
        "how to sell on amazon",
        "amazon fba for beginners",
        "start amazon fba",
        "amazon fba tutorial",
        "amazon seller account",
        "sell on amazon 2026",
        "amazon fba step by step",
    ],
    extended_keywords=[
        "amazon seller central",
        "first product on amazon",
        "amazon fba cost",
        "amazon fba worth it",
        "side hustle amazon",
        "amazon business beginner",
        "fba startup cost",
        "amazon fba mistakes",
        "product research for beginners",
        "amazon fba passive income",
    ],
    subreddits=["AmazonSeller", "FulfillmentByAmazon", "AmazonFBA", "sidehustle"],
))

# --- 2. Amazon FBA 运营卖家 ---
_register(Audience(
    id="fba_operator",
    name="Amazon FBA Operators",
    description="已经在运营 Amazon FBA 的中级卖家，关注优化和增长",
    core_keywords=[
        "amazon fba tips",
        "amazon product research",
        "amazon listing optimization",
        "amazon keyword ranking",
        "amazon fba inventory management",
        "amazon sales rank",
        "amazon buy box",
    ],
    extended_keywords=[
        "amazon a9 algorithm",
        "amazon cosmo algorithm",
        "amazon backend keywords",
        "fba restock",
        "amazon product launch",
        "amazon review strategy",
        "supplier negotiation",
        "amazon profit margin",
        "fba prep center",
        "amazon return rate",
        "amazon inventory performance index",
        "IPI score amazon",
    ],
    subreddits=["FulfillmentByAmazon", "AmazonSeller", "ecommerce"],
))

# --- 3. Amazon PPC / 广告专家 ---
_register(Audience(
    id="ppc_specialist",
    name="Amazon PPC & Advertising Specialists",
    description="专注 Amazon 广告投放和优化的卖家/运营人员",
    core_keywords=[
        "amazon ppc",
        "amazon advertising",
        "amazon sponsored products",
        "amazon sponsored brands",
        "amazon dsp",
        "amazon ppc strategy",
        "amazon acos",
    ],
    extended_keywords=[
        "amazon tacos",
        "amazon ppc optimization",
        "amazon ad spend",
        "amazon campaign structure",
        "amazon keyword targeting",
        "amazon product targeting",
        "amazon bid strategy",
        "amazon advertising console",
        "sponsored display amazon",
        "amazon ppc automation",
        "amazon dayparting",
        "amazon negative keywords",
        "amazon search term report",
    ],
    subreddits=["AmazonSeller", "FulfillmentByAmazon", "PPC"],
))

# --- 4. Amazon 品牌卖家 ---
_register(Audience(
    id="brand_owner",
    name="Amazon Brand Owners",
    description="拥有自有品牌、注重品牌建设和 A+ 内容的卖家",
    core_keywords=[
        "amazon brand registry",
        "amazon private label",
        "amazon a plus content",
        "amazon brand analytics",
        "amazon brand store",
        "amazon vine program",
        "build brand on amazon",
    ],
    extended_keywords=[
        "amazon brand protection",
        "amazon transparency program",
        "amazon brand referral bonus",
        "amazon posts",
        "amazon live",
        "amazon attribution",
        "premium a+ content",
        "brand story amazon",
        "amazon project zero",
        "ip protection amazon",
        "amazon counterfeit",
    ],
    subreddits=["AmazonSeller", "FulfillmentByAmazon", "ecommerce", "Entrepreneur"],
))

# --- 5. Amazon 批发/转售卖家 ---
_register(Audience(
    id="wholesale_reseller",
    name="Amazon Wholesale & Resellers",
    description="通过批发采购或零售套利在 Amazon 销售的卖家",
    core_keywords=[
        "amazon wholesale",
        "amazon retail arbitrage",
        "amazon online arbitrage",
        "wholesale on amazon",
        "amazon ungated categories",
        "amazon reselling",
    ],
    extended_keywords=[
        "amazon wholesale supplier",
        "amazon ungating",
        "restricted brands amazon",
        "amazon wholesale list",
        "retail arbitrage tips",
        "online arbitrage leads",
        "amazon flipping",
        "keepa amazon",
        "amazon price tracker",
        "tactical arbitrage",
    ],
    subreddits=["AmazonSeller", "Flipping", "ecommerce"],
))

# --- 6. 跨境/国际 Amazon 卖家 ---
_register(Audience(
    id="international_seller",
    name="Amazon International / Cross-Border Sellers",
    description="在多个 Amazon 站点运营或跨境销售的卖家",
    core_keywords=[
        "amazon global selling",
        "amazon europe seller",
        "amazon japan seller",
        "sell on amazon internationally",
        "amazon cross border",
        "amazon fba export",
    ],
    extended_keywords=[
        "amazon vat",
        "amazon uk seller",
        "amazon germany seller",
        "amazon pan-european fba",
        "amazon narf",
        "remote fulfillment amazon",
        "amazon unified account",
        "eori number amazon",
        "amazon canada seller",
        "amazon australia seller",
        "amazon middle east",
    ],
    subreddits=["AmazonSeller", "FulfillmentByAmazon", "ecommerce"],
))

# --- 7. Amazon 政策与新闻关注者 ---
_register(Audience(
    id="policy_watcher",
    name="Amazon Policy & News Watchers",
    description="持续关注 Amazon 政策变更、费用调整和平台更新的卖家",
    core_keywords=[
        "amazon seller news",
        "amazon fee changes",
        "amazon policy update",
        "amazon fba fee",
        "amazon seller update 2026",
        "amazon algorithm update",
    ],
    extended_keywords=[
        "amazon inbound placement fee",
        "amazon low inventory fee",
        "amazon referral fee",
        "amazon account suspension",
        "amazon seller performance",
        "amazon plan of action",
        "amazon appeal",
        "amazon account health",
        "amazon section 3 violation",
        "amazon ip complaint",
        "amazon new feature",
    ],
    subreddits=["AmazonSeller", "FulfillmentByAmazon"],
))

# --- 8. Amazon 工具与软件用户 ---
_register(Audience(
    id="tools_user",
    name="Amazon Seller Tools & Software Users",
    description="使用各种第三方工具辅助 Amazon 运营的卖家",
    core_keywords=[
        "amazon seller tools",
        "jungle scout",
        "helium 10",
        "amazon product research tool",
        "amazon keyword tool",
        "amazon repricer",
    ],
    extended_keywords=[
        "viral launch",
        "sellics",
        "sellerapp",
        "amazon seller software",
        "amazon analytics tool",
        "amazon chrome extension",
        "keepa",
        "camelcamelcamel",
        "amazon fba calculator",
        "inventory management software",
        "amazon accounting software",
        "amazon ai tools",
    ],
    subreddits=["AmazonSeller", "FulfillmentByAmazon", "ecommerce"],
))


def get_all_keywords() -> list[str]:
    """获取所有受众的关键词（去重）"""
    all_kw = set()
    for audience in AUDIENCES.values():
        all_kw.update(audience.all_keywords)
    return sorted(all_kw)


def get_all_subreddits() -> list[str]:
    """获取所有受众涉及的 subreddit（去重）"""
    subs = set()
    for audience in AUDIENCES.values():
        subs.update(audience.subreddits)
    return sorted(subs)


def get_audience_for_keyword(keyword: str) -> list[Audience]:
    """根据关键词反查所属受众"""
    keyword_lower = keyword.lower()
    matched = []
    for audience in AUDIENCES.values():
        for kw in audience.all_keywords:
            if kw.lower() in keyword_lower or keyword_lower in kw.lower():
                matched.append(audience)
                break
    return matched
