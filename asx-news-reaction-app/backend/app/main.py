from __future__ import annotations

import json
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import get_db, init_db
from .models import ListedCompany, ReactionAnalysis, Story
from .schemas import CompanyOut, RunResult, StoryOut
from .services.ingestion import IngestionService
from .services.sample_data import seed_demo_data
from .services.scheduler import start_scheduler

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    start_scheduler()


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "app": settings.app_name}


@app.get("/api/watchlist", response_model=list[CompanyOut])
def get_watchlist(db: Session = Depends(get_db)):
    service = IngestionService(db)
    companies = service.ensure_watchlist()
    return [CompanyOut(ticker=c.ticker, name=c.name, yahoo_symbol=c.yahoo_symbol) for c in companies]


@app.get("/api/stories", response_model=list[StoryOut])
def get_stories(
    ticker: str | None = Query(default=None, description="Optional ASX code, e.g. BHP"),
    category: str | None = Query(default=None, description="POSITIVE, NEGATIVE or NEUTRAL"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Story).options(joinedload(Story.analysis)).order_by(desc(Story.published_at)).limit(limit)
    if ticker:
        stmt = stmt.where(Story.ticker == ticker.upper())
    if category:
        stmt = stmt.join(ReactionAnalysis).where(ReactionAnalysis.category == category.upper())
    return list(db.scalars(stmt).unique())


@app.get("/api/stories/{story_id}", response_model=StoryOut)
def get_story(story_id: int, db: Session = Depends(get_db)):
    story = db.scalar(select(Story).options(joinedload(Story.analysis)).where(Story.id == story_id))
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@app.get("/api/stories/{story_id}/bars")
def get_story_bars(story_id: int, db: Session = Depends(get_db)):
    analysis = db.scalar(select(ReactionAnalysis).where(ReactionAnalysis.story_id == story_id))
    if not analysis or not analysis.bars_json:
        raise HTTPException(status_code=404, detail="Bars not found")
    return json.loads(analysis.bars_json)


@app.post("/api/run-now", response_model=RunResult)
async def run_now(db: Session = Depends(get_db)):
    service = IngestionService(db)
    result = await service.run_once()
    return result


@app.post("/api/seed-demo")
def seed_demo(db: Session = Depends(get_db)):
    return seed_demo_data(db)
