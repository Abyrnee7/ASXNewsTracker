export type Category = "POSITIVE" | "NEGATIVE" | "NEUTRAL";

export interface Analysis {
  pre_close: number | null;
  post_close: number | null;
  return_24h_pct: number | null;
  pre_volume: number | null;
  post_volume: number | null;
  volume_ratio: number | null;
  pre_trade_count: number | null;
  post_trade_count: number | null;
  trade_count_ratio: number | null;
  sentiment_score: number;
  price_score: number | null;
  activity_score: number | null;
  reaction_score: number;
  category: Category;
  explanation: string;
  bars_json: string | null;
  analysed_at: string;
}

export interface Story {
  id: number;
  ticker: string;
  headline: string;
  source: string;
  url: string;
  published_at: string;
  summary: string | null;
  analysis: Analysis | null;
}

export interface MarketBar {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  trade_count: number | null;
}
