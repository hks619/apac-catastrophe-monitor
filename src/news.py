import re
from datetime import datetime
from urllib.parse import quote_plus

import feedparser

_BASE = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"

PERIL_QUERIES = {
    "All Perils":        '"natural disaster" OR catastrophe OR hazard OR "disaster relief"',
    "Earthquake":        'earthquake seismic tremor magnitude',
    "Cyclone / Typhoon": 'typhoon OR cyclone OR hurricane OR "tropical storm"',
    "Wildfire":          'wildfire OR bushfire OR "forest fire"',
    "Flood":             'flood OR flooding OR "flash flood"',
    "Volcano":           'volcano OR eruption volcanic',
    "Drought":           'drought "water shortage" OR "crop failure"',
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
