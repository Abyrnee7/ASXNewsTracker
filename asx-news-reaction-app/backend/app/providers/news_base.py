from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsItem:
    ticker: str
    headline: str
    source: str
    url: str
    published_at: datetime
    summary: str | None = None
    raw_text: str | None = None


class NewsProvider:
    name = "base"

    async def fetch(self, ticker: str, company_name: str | None = None) -> list[NewsItem]:
        raise NotImplementedError
