# ASX News Reaction App

A starter full-stack app that monitors ASX-listed companies, collects announcements/news, measures the stock reaction from **24 hours before** to **24 hours after** the story timestamp, and classifies each story as **positive**, **negative** or **neutral** for the stock.

## What it does

- Runs an hourly ingestion job.
- Watches a configurable ASX ticker list.
- Pulls stories from:
  - ASX public announcement search pages, suitable for a prototype only.
  - GDELT global news, suitable for a free prototype news feed.
- Pulls 5-minute intraday OHLCV data using `yfinance`.
- Measures:
  - pre-event close vs post-event close
  - 24-hour reaction return
  - volume before vs after
  - trade-frequency proxy before vs after
- Classifies each story using:
  - headline/story sentiment
  - price reaction
  - trading activity change
- Provides a FastAPI backend and React dashboard.

## Important production note

For production-grade ASX monitoring, you should use licensed data feeds:

- **ASX ComNews** or another licensed ASX announcements provider for complete real-time announcements.
- **Iress, Refinitiv, FactSet, Morningstar, Bloomberg, ASX MarketSource or broker/vendor tick data** for true trade frequency / transaction count.

The included app uses public/free sources so you can build and test the workflow. The provider interfaces are separated so you can swap in licensed feeds without rewriting the whole app.

## Folder structure

```text
backend/
  app/
    providers/       # story and market data providers
    services/        # ingestion, scheduler, analysis logic
    main.py          # FastAPI routes
frontend/
  src/               # React dashboard
```

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Backend runs at:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

### 2. Frontend

Open a second terminal:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

### 3. Load test data

In the frontend, click **Seed demo**.

Or call:

```bash
curl -X POST http://localhost:8000/api/seed-demo
```

### 4. Run ingestion manually

```bash
curl -X POST http://localhost:8000/api/run-now
```

The scheduler also runs automatically once per hour at minute 5 UTC by default.

## Configuration

Edit `backend/.env`:

```env
WATCHLIST=BHP,CBA,JBH,WDS,FMG,CSL
ENABLE_ASX_PUBLIC_ANNOUNCEMENTS=true
ENABLE_GDELT_NEWS=true
SCHEDULER_ENABLED=true
SCHEDULER_MINUTE=5
EVENT_WINDOW_HOURS=24
INTRADAY_INTERVAL=5m
```

The app converts ASX ticker codes into Yahoo symbols using `.AX`, for example:

```text
BHP -> BHP.AX
JBH -> JBH.AX
```

## How the classification works

The backend creates one `ReactionAnalysis` record for each story:

```text
reaction_score = 45% news sentiment + 40% price reaction + 15% trading activity
```

Then:

```text
>= +0.12  -> POSITIVE
<= -0.12  -> NEGATIVE
otherwise -> NEUTRAL
```

You can adjust these weights inside:

```text
backend/app/services/analyser.py
```

## True trade frequency vs proxy

The app schema supports a real `trade_count` field. However, free OHLCV data usually provides volume, not individual trades. Until you connect a tick-level feed, the app uses an **active-bar count** as a trade-frequency proxy.

To add true trade count, create a new market provider that returns `MarketBar(trade_count=...)` in:

```text
backend/app/providers/market_base.py
```

and wire it into:

```text
backend/app/services/ingestion.py
```

## Production upgrades worth doing next

- Add a licensed ASX announcements provider.
- Add a tick-level ASX trade provider.
- Store company names and aliases to improve news matching.
- Add market-adjusted returns using the S&P/ASX 200 as benchmark.
- Add event de-duplication by timestamp/headline similarity.
- Use an LLM classifier with a strict JSON output schema for better story interpretation.
- Add user login and portfolio/watchlist management.
- Add alerts when a major negative story breaks with abnormal volume.

## Disclaimer

This app is for research and workflow prototyping. It is not financial advice and should not be used for live trading without licensed data, validation and compliance review.
