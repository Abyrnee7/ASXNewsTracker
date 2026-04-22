from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

import httpx
from dateutil import parser as date_parser

from .news_base import NewsItem, NewsProvider


class GDELTNewsProvider(NewsProvider):
    """Free global-news provider using GDELT DOC 2.0."""

    name = "GDELT news"

    async def fetch(self, ticker: str, company_name: str | None = None) -> list[NewsItem]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=2)
        terms = [f'"{ticker.upper()}" "ASX"']
        if company_name:
            terms.append(f'"{company_name}"')
        query = " OR ".join(terms)
        url = (
            "https://api.gdeltproject.org/api/v2/doc/doc"
            f"?query={quote_plus(query)}"
            "&mode=artlist&format=json&maxrecords=25&sort=hybridrel"
            f"&startdatetime={start.strftime('%Y%m%d%H%M%S')}"
            f"&enddatetime={end.strftime('%Y%m%d%H%M%S')}"
        )
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": "asx-news-reaction/0.1"}) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        articles = data.get("articles", []) if isinstance(data, dict) else []
        items: list[NewsItem] = []
        for article in articles:
            title = article.get("title")
            article_url = article.get("url")
            if not title or not article_url:
                continue
            seen = article.get("seendate") or article.get("seendatefull")
            try:
                published = date_parser.parse(seen).astimezone(timezone.utc) if seen else datetime.now(timezone.utc)
            except Exception:
                published = datetime.now(timezone.utc)
            items.append(
                NewsItem(
                    ticker=ticker.upper(),
                    headline=title.strip(),
                    source=article.get("domain") or self.name,
                    url=article_url,
                    published_at=published,
                    summary=article.get("snippet") or None,
                )
            )
        return items
