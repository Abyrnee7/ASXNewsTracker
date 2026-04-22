from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from .market_base import MarketBar, MarketDataProvider


class YFinanceMarketProvider(MarketDataProvider):
    """Intraday OHLCV provider. Good for prototyping; not a licensed market-data feed."""

    name = "yfinance"

    def fetch_bars(self, symbol: str, start: datetime, end: datetime, interval: str = "5m") -> list[MarketBar]:
        start_utc = start.astimezone(timezone.utc).replace(tzinfo=None)
        end_utc = end.astimezone(timezone.utc).replace(tzinfo=None)
        df = yf.download(
            symbol,
            start=start_utc,
            end=end_utc,
            interval=interval,
            progress=False,
            auto_adjust=False,
            prepost=False,
            threads=False,
        )
        if df.empty:
            return []

        # yfinance can return MultiIndex columns depending on version/ticker count.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]

        bars: list[MarketBar] = []
        for idx, row in df.dropna(subset=["Open", "High", "Low", "Close"]).iterrows():
            ts = idx.to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
            bars.append(
                MarketBar(
                    ts=ts,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row.get("Volume", 0) or 0),
                    trade_count=None,
                )
            )
        return bars
