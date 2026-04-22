from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ListedCompany, ReactionAnalysis, Story


def seed_demo_data(db: Session) -> dict:
    """Create deterministic demo data so the dashboard works before API keys/data access are configured."""
    random.seed(7)
    inserted = 0
    tickers = ["BHP", "CBA", "JBH", "WDS"]
    headlines = {
        "BHP": "BHP announces stronger quarterly production and higher copper guidance",
        "CBA": "CBA flags softer housing credit growth and margin pressure",
        "JBH": "JB Hi-Fi upgrades sales outlook after stronger consumer electronics demand",
        "WDS": "Woodside reports LNG project delay and cost increase",
    }
    categories = {"BHP": "POSITIVE", "CBA": "NEGATIVE", "JBH": "POSITIVE", "WDS": "NEGATIVE"}
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    for ticker in tickers:
        company = db.scalar(select(ListedCompany).where(ListedCompany.ticker == ticker))
        if not company:
            db.add(ListedCompany(ticker=ticker, yahoo_symbol=f"{ticker}.AX"))

        story = db.scalar(select(Story).where(Story.url == f"demo://{ticker.lower()}-story"))
        if story:
            continue
        published_at = now - timedelta(hours=8 + tickers.index(ticker) * 3)
        story = Story(
            ticker=ticker,
            headline=headlines[ticker],
            source="Demo seed",
            url=f"demo://{ticker.lower()}-story",
            published_at=published_at,
            summary="Synthetic demo story. Replace with ASX ComNews/public announcements and licensed market data in production.",
        )
        db.add(story)
        db.commit()
        db.refresh(story)

        positive = categories[ticker] == "POSITIVE"
        price = 100 + random.random() * 10
        bars = []
        for i in range(-24, 25):
            drift = (0.0015 * i if positive else -0.0013 * i) if i >= 0 else 0
            close = price * (1 + drift + random.uniform(-0.002, 0.002))
            volume = 10000 + (3500 if i >= 0 else 0) + random.randint(0, 3000)
            bars.append({
                "ts": (published_at + timedelta(hours=i)).isoformat(),
                "open": close * 0.997,
                "high": close * 1.006,
                "low": close * 0.994,
                "close": close,
                "volume": volume,
                "trade_count": random.randint(90, 220) + (60 if i >= 0 else 0),
            })
        pre_close = bars[23]["close"]
        post_close = bars[-1]["close"]
        ret = ((post_close / pre_close) - 1) * 100
        pre_volume = sum(b["volume"] for b in bars[:24])
        post_volume = sum(b["volume"] for b in bars[24:])
        pre_trades = sum(b["trade_count"] for b in bars[:24])
        post_trades = sum(b["trade_count"] for b in bars[24:])
        score = 0.62 if positive else -0.58
        analysis = ReactionAnalysis(
            story_id=story.id,
            pre_close=pre_close,
            post_close=post_close,
            return_24h_pct=ret,
            pre_volume=pre_volume,
            post_volume=post_volume,
            volume_ratio=post_volume / pre_volume,
            pre_trade_count=pre_trades,
            post_trade_count=post_trades,
            trade_count_ratio=post_trades / pre_trades,
            sentiment_score=0.51 if positive else -0.47,
            price_score=0.54 if positive else -0.49,
            activity_score=0.22 if positive else -0.19,
            reaction_score=score,
            category=categories[ticker],
            explanation="Demo classification combining synthetic sentiment, price reaction and trade-frequency metrics.",
            bars_json=json.dumps(bars),
        )
        db.add(analysis)
        db.commit()
        inserted += 1
    return {"inserted": inserted}
