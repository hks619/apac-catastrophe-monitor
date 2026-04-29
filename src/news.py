import re
from datetime import datetime
from urllib.parse import quote_plus

import feedparser

_BASE = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"

_REGION_TERMS = {
    "Global":        "",
    "APAC":          '"Asia Pacific" OR APAC OR Japan OR Philippines OR Indonesia OR Australia',
    "Europe":        "Europe OR Turkey OR Greece OR Italy OR Balkans OR Iberia",
    "Africa":        "Africa OR Mozambique OR Madagascar OR Ethiopia OR Kenya OR Nigeria",
    "North America": '"North America" OR "United States" OR Canada OR Mexico OR Caribbean',
    "South America": '"South America" OR Brazil OR Colombia OR Peru OR Chile OR Argentina',
    "Antarctica":    "Antarctica OR Antarctic",
}


def get_peril_queries(region: str = "Global") -> dict[str, str]:
    geo = _REGION_TERMS.get(region, "")

    def q(*terms) -> str:
        base = " OR ".join(terms)
        return f"({base}) {geo}".strip() if geo else base

    return {
        "All Perils":        q("disaster", "catastrophe", "natural hazard"),
        "Earthquake":        q("earthquake", "tremor", "seismic"),
        "Cyclone / Typhoon": q("typhoon", "cyclone", "hurricane", "tropical storm"),
        "Wildfire":          q("wildfire", "bushfire", "forest fire"),
        "Flood":             q("flood", "flooding", "flash flood"),
        "Volcano":           q("volcano", "eruption", "volcanic"),
        "Drought":           q("drought", "water shortage"),
    }


def fetch_news(query: str, max_results: int = 25) -> list[dict]:
    url = _BASE.format(q=quote_plus(query))
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:max_results]:
        published = ""
        if entry.get("published_parsed"):
            published = datetime(*entry.published_parsed[:6]).strftime("%d %b %Y, %H:%M UTC")

        source = ""
        src = entry.get("source")
        if isinstance(src, dict):
            source = src.get("title", "")

        summary = re.sub(r"<[^>]+>", "", entry.get("summary", "")).strip()[:350]

        articles.append({
            "title":     entry.get("title", ""),
            "link":      entry.get("link", ""),
            "published": published,
            "source":    source,
            "summary":   summary,
        })
    return articles
