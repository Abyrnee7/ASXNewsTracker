import type { MarketBar, Story } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function getStories(filters: { ticker?: string; category?: string } = {}) {
  const params = new URLSearchParams();
  if (filters.ticker) params.set("ticker", filters.ticker);
  if (filters.category) params.set("category", filters.category);
  params.set("limit", "100");
  return request<Story[]>(`/api/stories?${params.toString()}`);
}

export function getBars(storyId: number) {
  return request<MarketBar[]>(`/api/stories/${storyId}/bars`);
}

export function runNow() {
  return request<{ inserted_stories: number; analysed_stories: number; errors: string[] }>("/api/run-now", {
    method: "POST",
  });
}

export function seedDemo() {
  return request<{ inserted: number }>("/api/seed-demo", { method: "POST" });
}
