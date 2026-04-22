from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from ..models import ReactionAnalysis, Story
from ..providers.market_base import MarketBar, MarketDataProvider

sentiment_analyser = SentimentIntensityAnalyzer()


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    if denominator <= 0:
        return None
    return numerator / denominator


def _tanh_scaled(value: float | None, divisor: float) -> float | None:
    if value is None:
        return None
    return math.tanh(value / divisor)


def _bar_json(bars: list[MarketBar]) -> str:
    return json.dumps(
        [
            {
                "ts": bar.ts.isoformat(),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "trade_count": bar.trade_count,
            }
            for bar in bars
        ]
    )


class StoryReactionAnalyser:
    def __init__(self, market_provider: MarketDataProvider, window_hours: int = 24, interval: str = "5m"):
        self.market_provider = market_provider
        self.window_hours = window_hours
        self.interval = interval

    def analyse(self, story: Story, yahoo_symbol: str) -> ReactionAnalysis:
        event_time = story.published_at
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        event_time = event_time.astimezone(timezone.utc)

        start = event_time - timedelta(hours=self.window_hours)
        end = event_time + timedelta(hours=self.window_hours)
        bars = self.market_provider.fetch_bars(yahoo_symbol, start, end, self.interval)

        pre_bars = [bar for bar in bars if start <= bar.ts < event_time]
        post_bars = [bar for bar in bars if event_time <= bar.ts <= end]

        pre_close = pre_bars[-1].close if pre_bars else None
        post_close = post_bars[-1].close if post_bars else None
        return_pct = ((post_close / pre_close) - 1) * 100 if pre_close and post_close else None

        pre_volume = sum(bar.volume for bar in pre_bars) if pre_bars else None
        post_volume = sum(bar.volume for bar in post_bars) if post_bars else None
        volume_ratio = _safe_ratio(post_volume, pre_volume)

        # True trade frequency requires tick/trade-count data. OHLCV providers do not always include it.
        if any(bar.trade_count is not None for bar in bars):
            pre_trade_count = sum(bar.trade_count or 0 for bar in pre_bars) if pre_bars else None
            post_trade_count = sum(bar.trade_count or 0 for bar in post_bars) if post_bars else None
        else:
            # Fallback proxy: count active intraday bars. This is NOT true trade count, but keeps the UI functional.
            pre_trade_count = sum(1 for bar in pre_bars if bar.volume > 0) if pre_bars else None
            post_trade_count = sum(1 for bar in post_bars if bar.volume > 0) if post_bars else None
        trade_count_ratio = _safe_ratio(post_trade_count, pre_trade_count)

        text = " ".join(x for x in [story.headline, story.summary, story.raw_text] if x)
        sentiment_score = float(sentiment_analyser.polarity_scores(text)["compound"])
        price_score = _tanh_scaled(return_pct, 5.0)

        # Elevated activity strengthens the direction of the price move. If price is missing, it is neutral.
        if volume_ratio and volume_ratio > 0 and return_pct is not None:
            activity_score = math.tanh(math.log(volume_ratio)) * (1 if return_pct >= 0 else -1)
        else:
            activity_score = None

        reaction_score = 0.45 * sentiment_score
        if price_score is not None:
            reaction_score += 0.40 * price_score
        if activity_score is not None:
            reaction_score += 0.15 * activity_score

        if reaction_score >= 0.12:
            category = "POSITIVE"
        elif reaction_score <= -0.12:
            category = "NEGATIVE"
        else:
            category = "NEUTRAL"

        explanation_bits = [f"Headline/news sentiment score: {sentiment_score:.2f}."]
        if return_pct is not None:
            explanation_bits.append(f"Price moved {return_pct:.2f}% from the last pre-event bar to the final post-event bar.")
        else:
            explanation_bits.append("Price reaction could not be measured because intraday bars were unavailable for the full window.")
        if volume_ratio is not None:
            explanation_bits.append(f"Post-event volume was {volume_ratio:.2f}x the pre-event window.")
        if trade_count_ratio is not None:
            explanation_bits.append(f"Trade-frequency proxy changed by {trade_count_ratio:.2f}x.")
        explanation_bits.append("Classification combines sentiment, price reaction and trading activity around the event window.")

        return ReactionAnalysis(
            story_id=story.id,
            pre_close=pre_close,
            post_close=post_close,
            return_24h_pct=return_pct,
            pre_volume=pre_volume,
            post_volume=post_volume,
            volume_ratio=volume_ratio,
            pre_trade_count=pre_trade_count,
            post_trade_count=post_trade_count,
            trade_count_ratio=trade_count_ratio,
            sentiment_score=sentiment_score,
            price_score=price_score,
            activity_score=activity_score,
            reaction_score=reaction_score,
            category=category,
            explanation=" ".join(explanation_bits),
            bars_json=_bar_json(bars),
        )
