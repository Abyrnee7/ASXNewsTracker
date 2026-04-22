from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pre_close: float | None
    post_close: float | None
    return_24h_pct: float | None
    pre_volume: float | None
    post_volume: float | None
    volume_ratio: float | None
    pre_trade_count: float | None
    post_trade_count: float | None
    trade_count_ratio: float | None
    sentiment_score: float
    price_score: float | None
    activity_score: float | None
    reaction_score: float
    category: str
    explanation: str
    bars_json: str | None
    analysed_at: datetime


class StoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    headline: str
    source: str
    url: str
    published_at: datetime
    summary: str | None
    analysis: AnalysisOut | None = None


class CompanyOut(BaseModel):
    ticker: str
    name: str | None = None
    yahoo_symbol: str


class RunResult(BaseModel):
    inserted_stories: int
    analysed_stories: int
    errors: list[str]
