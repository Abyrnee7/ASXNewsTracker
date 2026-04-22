from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ListedCompany(Base):
    __tablename__ = "listed_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    yahoo_symbol: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Story(Base):
    __tablename__ = "stories"
    __table_args__ = (
        UniqueConstraint("ticker", "url", name="uq_story_ticker_url"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(12), index=True)
    headline: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(120), index=True)
    url: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    analysis: Mapped["ReactionAnalysis"] = relationship(back_populates="story", uselist=False, cascade="all, delete-orphan")


class ReactionAnalysis(Base):
    __tablename__ = "reaction_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), unique=True, index=True)

    pre_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    post_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_24h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    pre_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    post_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    pre_trade_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    post_trade_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    trade_count_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    sentiment_score: Mapped[float] = mapped_column(Float)
    price_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    activity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_score: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(20), index=True)  # POSITIVE / NEGATIVE / NEUTRAL
    explanation: Mapped[str] = mapped_column(Text)
    bars_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    story: Mapped[Story] = relationship(back_populates="analysis")
