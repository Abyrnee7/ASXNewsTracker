from datetime import datetime, timezone
from urllib.parse import urljoin
import re

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from .news_base import NewsItem, NewsProvider


class ASXPublicAnnouncementsProvider(NewsProvider):
    """Demo parser for public ASX announcement search pages.

    Production note: for live/complete coverage, use ASX ComNews or another licensed
    announcement feed. The public HTML can change and should not be treated as an SLA-backed API.
    """

    name = "ASX public announcements"
    base_url = "https://www.asx.com.au"

    async def fetch(self, ticker: str, company_name: str | None = None) -> list[NewsItem]:
        url = (
            "https://www.asx.com.au/asx/v2/statistics/announcements.do"
            f"?asxCode={ticker.upper()}&by=asxCode&period=D&timeframe=D"
        )
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": "asx-news-reaction/0.1"}) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        items: list[NewsItem] = []

        for row in soup.find_all("tr"):
            text = " ".join(row.get_text(" ", strip=True).split())
            link = row.find("a", href=True)
            if not link:
                continue

            href = link.get("href", "")
            if not ("announcement" in href.lower() or "asxpdf" in href.lower() or href.lower().endswith(".pdf")):
                continue

            headline = link.get_text(" ", strip=True) or text
            headline = re.sub(r"\s+", " ", headline).strip()
            if not headline or len(headline) < 4:
                continue

            published = self._extract_date(text) or datetime.now(timezone.utc)
            absolute_url = urljoin(self.base_url, href)

            items.append(
                NewsItem(
                    ticker=ticker.upper(),
                    headline=headline,
                    source=self.name,
                    url=absolute_url,
                    published_at=published,
                    summary=text if text != headline else None,
                )
            )

        # Fallback for less table-like markup.
        if not items:
            for link in soup.find_all("a", href=True):
                headline = link.get_text(" ", strip=True)
                href = link.get("href", "")
                if not headline or not ("announcement" in href.lower() or "asxpdf" in href.lower() or href.lower().endswith(".pdf")):
                    continue
                items.append(
                    NewsItem(
                        ticker=ticker.upper(),
                        headline=re.sub(r"\s+", " ", headline).strip(),
                        source=self.name,
                        url=urljoin(self.base_url, href),
                        published_at=datetime.now(timezone.utc),
                    )
                )

        # De-dupe by URL.
        unique: dict[str, NewsItem] = {}
        for item in items:
            unique[item.url] = item
        return list(unique.values())

    @staticmethod
    def _extract_date(text: str) -> datetime | None:
        candidates = re.findall(
            r"(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})(?:\s+\d{1,2}:\d{2}(?:\s?[AP]M)?)?",
            text,
        )
        for candidate in candidates:
            try:
                dt = date_parser.parse(candidate, dayfirst=True)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                continue
        return None
