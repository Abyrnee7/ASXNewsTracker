from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketBar:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: float | None = None


class MarketDataProvider:
    name = "base"

    def fetch_bars(self, symbol: str, start: datetime, end: datetime, interval: str = "5m") -> list[MarketBar]:
        raise NotImplementedError
