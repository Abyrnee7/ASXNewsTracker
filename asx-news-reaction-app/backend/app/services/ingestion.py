from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import ListedCompany, ReactionAnalysis, Story
from ..providers.asx_announcements import ASXPublicAnnouncementsProvider
from ..providers.gdelt import GDELTNewsProvider
from ..providers.news_base import NewsProvider
from ..providers.yfinance_market import YFinanceMarketProvider
from .analyser import StoryReactionAnalyser


class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.news_providers: list[NewsProvider] = []
        if self.settings.enable_asx_public_announcements:
            self.news_providers.append(ASXPublicAnnouncementsProvider())
        if self.settings.enable_gdelt_news:
            self.news_providers.append(GDELTNewsProvider())

        self.market_provider = YFinanceMarketProvider()
        self.analyser = StoryReactionAnalyser(
            market_provider=self.market_provider,
            window_hours=self.settings.event_window_hours,
            interval=self.settings.intraday_interval,
        )

    def ensure_watchlist(self) -> list[ListedCompany]:
        companies: list[ListedCompany] = []
        for ticker in self.settings.watchlist_codes:
            company = self.db.scalar(select(ListedCompany).where(ListedCompany.ticker == ticker))
            if not company:
                company = ListedCompany(ticker=ticker, yahoo_symbol=f"{ticker}.AX")
                self.db.add(company)
                self.db.commit()
                self.db.refresh(company)
            companies.append(company)
        return companies

    async def run_once(self) -> dict:
        inserted = 0
        analysed = 0
        errors: list[str] = []
        companies = self.ensure_watchlist()

        for company in companies:
            for provider in self.news_providers:
                try:
                    news_items = await provider.fetch(company.ticker, company.name)
                except Exception as exc:  # Keep hourly job alive even when one provider fails.
                    errors.append(f"{provider.name} / {company.ticker}: {exc}")
                    continue

                for item in news_items:
                    story = Story(
                        ticker=item.ticker,
                        headline=item.headline[:500],
                        source=item.source[:120],
                        url=item.url,
                        published_at=item.published_at,
                        summary=item.summary,
                        raw_text=item.raw_text,
                    )
                    self.db.add(story)
                    try:
                        self.db.commit()
                        self.db.refresh(story)
                        inserted += 1
                    except IntegrityError:
                        self.db.rollback()
                        story = self.db.scalar(
                            select(Story).where(Story.ticker == item.ticker, Story.url == item.url)
                        )
                    except Exception as exc:
                        self.db.rollback()
                        errors.append(f"Saving story {company.ticker}: {exc}")
                        continue

                    if not story:
                        continue
                    existing_analysis = self.db.scalar(select(ReactionAnalysis).where(ReactionAnalysis.story_id == story.id))
                    if existing_analysis:
                        continue
                    try:
                        analysis = self.analyser.analyse(story, company.yahoo_symbol)
                        self.db.add(analysis)
                        self.db.commit()
                        analysed += 1
                    except Exception as exc:
                        self.db.rollback()
                        errors.append(f"Analysing {story.ticker} story {story.id}: {exc}")

        return {"inserted_stories": inserted, "analysed_stories": analysed, "errors": errors}
