import { useEffect, useMemo, useState } from "react";
import { Activity, Newspaper, RefreshCw, TrendingDown, TrendingUp } from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getBars, getStories, runNow, seedDemo } from "./api";
import type { Category, MarketBar, Story } from "./types";

const categories: Array<"ALL" | Category> = ["ALL", "POSITIVE", "NEGATIVE", "NEUTRAL"];

function fmt(value: number | null | undefined, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function pct(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value >= 0 ? "+" : ""}${fmt(value)}%`;
}

function categoryClass(category?: string) {
  if (category === "POSITIVE") return "pill positive";
  if (category === "NEGATIVE") return "pill negative";
  return "pill neutral";
}

function StoryCard({ story, selected, onSelect }: { story: Story; selected: boolean; onSelect: () => void }) {
  const analysis = story.analysis;
  return (
    <button className={`story-card ${selected ? "selected" : ""}`} onClick={onSelect}>
      <div className="story-topline">
        <span className="ticker">{story.ticker}</span>
        <span className={categoryClass(analysis?.category)}>{analysis?.category ?? "UNANALYSED"}</span>
      </div>
      <h3>{story.headline}</h3>
      <p className="muted">
        {story.source} · {new Date(story.published_at).toLocaleString()}
      </p>
      <div className="metric-row">
        <span>24h return</span>
        <strong className={(analysis?.return_24h_pct ?? 0) >= 0 ? "up" : "down"}>{pct(analysis?.return_24h_pct)}</strong>
      </div>
      <div className="metric-row">
        <span>Volume ratio</span>
        <strong>{fmt(analysis?.volume_ratio)}x</strong>
      </div>
    </button>
  );
}

function StatCard({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default function App() {
  const [stories, setStories] = useState<Story[]>([]);
  const [selected, setSelected] = useState<Story | null>(null);
  const [bars, setBars] = useState<MarketBar[]>([]);
  const [ticker, setTicker] = useState("");
  const [category, setCategory] = useState<"ALL" | Category>("ALL");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function loadStories() {
    setLoading(true);
    try {
      const data = await getStories({ ticker: ticker || undefined, category: category === "ALL" ? undefined : category });
      setStories(data);
      setSelected((current) => current && data.find((s) => s.id === current.id) ? current : data[0] ?? null);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Failed to load stories");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStories();
    const id = window.setInterval(loadStories, 60 * 60 * 1000);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category]);

  useEffect(() => {
    if (!selected) {
      setBars([]);
      return;
    }
    getBars(selected.id)
      .then(setBars)
      .catch(() => setBars([]));
  }, [selected]);

  const chartData = useMemo(() => {
    return bars.map((bar) => ({
      time: new Date(bar.ts).toLocaleString(undefined, { day: "2-digit", hour: "2-digit", minute: "2-digit" }),
      close: Number(bar.close.toFixed(3)),
      volume: bar.volume,
      trade_count: bar.trade_count ?? 0,
    }));
  }, [bars]);

  const totals = useMemo(() => {
    const positive = stories.filter((s) => s.analysis?.category === "POSITIVE").length;
    const negative = stories.filter((s) => s.analysis?.category === "NEGATIVE").length;
    const avgReturn = stories.length
      ? stories.reduce((acc, s) => acc + (s.analysis?.return_24h_pct ?? 0), 0) / stories.length
      : 0;
    return { positive, negative, avgReturn };
  }, [stories]);

  async function handleRunNow() {
    setLoading(true);
    setMessage("Running ingestion and analysis...");
    try {
      const result = await runNow();
      setMessage(`Inserted ${result.inserted_stories}, analysed ${result.analysed_stories}. ${result.errors.length ? "Some providers returned errors." : ""}`);
      await loadStories();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Run failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleSeedDemo() {
    setLoading(true);
    try {
      const result = await seedDemo();
      setMessage(`Demo data inserted: ${result.inserted}`);
      await loadStories();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not seed demo data");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <div className="eyebrow"><Newspaper size={16} /> ASX market-news reaction monitor</div>
          <h1>News, announcements and stock reaction in one dashboard.</h1>
          <p>
            Pulls ASX announcements and news, measures 24 hours before and after each event, then classifies the story as positive, negative or neutral.
          </p>
        </div>
        <div className="actions">
          <button className="secondary" onClick={handleSeedDemo} disabled={loading}>Seed demo</button>
          <button className="primary" onClick={handleRunNow} disabled={loading}>
            <RefreshCw size={16} /> Run now
          </button>
        </div>
      </header>

      <section className="stats-grid">
        <StatCard label="Stories loaded" value={String(stories.length)} icon={<Newspaper size={20} />} />
        <StatCard label="Positive" value={String(totals.positive)} icon={<TrendingUp size={20} />} />
        <StatCard label="Negative" value={String(totals.negative)} icon={<TrendingDown size={20} />} />
        <StatCard label="Avg 24h return" value={pct(totals.avgReturn)} icon={<Activity size={20} />} />
      </section>

      <section className="toolbar">
        <input
          placeholder="Filter ticker e.g. BHP"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && loadStories()}
        />
        <button className="secondary" onClick={loadStories}>Apply</button>
        <div className="tabs">
          {categories.map((cat) => (
            <button key={cat} className={category === cat ? "active" : ""} onClick={() => setCategory(cat)}>{cat}</button>
          ))}
        </div>
      </section>

      {message && <div className="message">{message}</div>}

      <main className="content-grid">
        <aside className="story-list">
          {stories.map((story) => (
            <StoryCard key={story.id} story={story} selected={story.id === selected?.id} onSelect={() => setSelected(story)} />
          ))}
          {!stories.length && <div className="empty">No stories yet. Use “Seed demo” or “Run now”.</div>}
        </aside>

        <section className="detail-panel">
          {selected ? (
            <>
              <div className="detail-header">
                <div>
                  <span className="ticker large">{selected.ticker}</span>
                  <h2>{selected.headline}</h2>
                  <a href={selected.url} target="_blank" rel="noreferrer">Open source</a>
                </div>
                <span className={categoryClass(selected.analysis?.category)}>{selected.analysis?.category ?? "UNANALYSED"}</span>
              </div>

              <div className="analysis-grid">
                <div><span>Reaction score</span><strong>{fmt(selected.analysis?.reaction_score, 3)}</strong></div>
                <div><span>Sentiment</span><strong>{fmt(selected.analysis?.sentiment_score, 3)}</strong></div>
                <div><span>Return</span><strong>{pct(selected.analysis?.return_24h_pct)}</strong></div>
                <div><span>Trade freq. ratio</span><strong>{fmt(selected.analysis?.trade_count_ratio)}x</strong></div>
              </div>

              <p className="explanation">{selected.analysis?.explanation}</p>

              <div className="chart-card">
                <h3>Price reaction</h3>
                <ResponsiveContainer width="100%" height={260}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" minTickGap={28} />
                    <YAxis domain={["auto", "auto"]} />
                    <Tooltip />
                    <Area type="monotone" dataKey="close" strokeWidth={2} fillOpacity={0.15} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="chart-card">
                <h3>Trading activity</h3>
                <ResponsiveContainer width="100%" height={230}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" minTickGap={28} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="volume" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : (
            <div className="empty big">Select a story to view the reaction analysis.</div>
          )}
        </section>
      </main>
    </div>
  );
}
