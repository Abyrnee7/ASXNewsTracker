import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import get_settings
from ..db import SessionLocal
from .ingestion import IngestionService

scheduler = BackgroundScheduler(timezone="UTC")


def _run_hourly_job() -> None:
    async def runner():
        with SessionLocal() as db:
            service = IngestionService(db)
            await service.run_once()

    asyncio.run(runner())


def start_scheduler() -> None:
    settings = get_settings()
    if not settings.scheduler_enabled or scheduler.running:
        return
    scheduler.add_job(
        _run_hourly_job,
        CronTrigger(minute=settings.scheduler_minute),
        id="hourly-ingestion",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
