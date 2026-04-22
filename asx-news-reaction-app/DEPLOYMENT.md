# Deployment guide

This project has two separate apps:

- `backend` = FastAPI API, database access and hourly scheduler
- `frontend` = React/Vite website dashboard

Do not upload the ZIP directly to Wix, Squarespace or Webflow. Upload it to GitHub first, then connect the services below.

## Recommended setup

### 1. Backend on Render

Create a new Render Web Service from your GitHub repo.

Settings:

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Python version: `3.12.8`

Environment variables:

```env
WATCHLIST=BHP,CBA,JBH,WDS,FMG,CSL
SCHEDULER_ENABLED=true
SCHEDULER_MINUTE=5
EVENT_WINDOW_HOURS=24
INTRADAY_INTERVAL=5m
ENABLE_ASX_PUBLIC_ANNOUNCEMENTS=true
ENABLE_GDELT_NEWS=true
CORS_ORIGINS=https://YOUR-VERCEL-APP.vercel.app,http://localhost:5173
DATABASE_URL=sqlite:///./asx_reactions.db
```

For production, use Postgres instead of SQLite:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

### 2. Frontend on Vercel

Create a new Vercel project from the same GitHub repo.

Settings:

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`

Environment variable:

```env
VITE_API_BASE=https://YOUR-RENDER-BACKEND.onrender.com
```

### 3. Test it

Open your frontend URL and click:

- `Seed demo` first
- then `Run now`

If the frontend loads but the buttons fail, it is usually a CORS or API URL issue. Make sure:

- frontend `VITE_API_BASE` equals the backend URL exactly
- backend `CORS_ORIGINS` includes the frontend URL exactly
- backend `/api/health` opens in the browser

## Local run

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
