import re
from datetime import datetime
from urllib.parse import quote_plus

import feedparser

_BASE = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"

PERIL_QUERIES = {
    "All Perils":        '"Asia Pacific" OR APAC disaster OR catastrophe OR hazard',
    "Earthquake":        'earthquake "Asia Pacific" OR Japan OR Philippines OR Indonesia OR "New Zealand"',
    "Cyclone / Typhoon": 'typhoon OR cyclone "Asia Pacific" OR Pacific OR "Indian Ocean" OR "Bay of Bengal"',
    "Wildfire":          'wildfire OR bushfire "Asia Pacific" OR Australia OR Indonesia OR "Southeast Asia"',
    "Flood":             'flood "Asia Pacific" OR Bangladesh OR India OR China OR Vietnam OR Thailand',
    "Volcano":           'volcano eruption "Asia Pacific" OR Indonesia OR Philippines OR Japan OR "Papua New Guinea"',
    "Drought":           'drought "Asia Pacific" OR Australia OR India OR China',
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
