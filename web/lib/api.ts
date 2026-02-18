const API_BASE = "/api";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

// ── Types ──

export interface Audience {
  id: string;
  name: string;
  description: string;
  core_keywords: string[];
  extended_keywords: string[];
  subreddits: string[];
  is_active: boolean;
  keyword_count: number;
}

export interface ScrapeJob {
  id: number;
  audience_id: string;
  status: "pending" | "running" | "completed" | "failed";
  total_raw: number;
  total_filtered: number;
  total_deduped: number;
  total_clusters: number;
  total_ideas: number;
  error_message: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface TopicCluster {
  id: number;
  job_id: number;
  cluster_index: number;
  label: string;
  size: number;
  total_engagement: number;
  avg_engagement: number;
  sources: string[];
  top_titles: string[];
  representative_title: string;
  representative_body: string;
  created_at: string;
}

export interface ContentIdea {
  id: number;
  job_id: number;
  cluster_id: number;
  audience_id: string;
  format_type: string;
  topic_label: string;
  generated_content: string;
  source_urls: string[];
  is_favorite: boolean;
  is_published: boolean;
  notes: string;
  created_at: string;
}

export interface DashboardStats {
  total_jobs: number;
  total_contents: number;
  total_clusters: number;
  total_ideas: number;
  active_audiences: number;
  recent_jobs: ScrapeJob[];
  top_topics: TopicCluster[];
}

// ── API Functions ──

export const api = {
  dashboard: {
    stats: () => fetchAPI<DashboardStats>("/dashboard/stats"),
  },
  audiences: {
    list: () => fetchAPI<Audience[]>("/audiences/"),
    get: (id: string) => fetchAPI<Audience>(`/audiences/${id}`),
  },
  jobs: {
    list: (params?: string) => fetchAPI<ScrapeJob[]>(`/jobs/${params ? `?${params}` : ""}`),
    get: (id: number) => fetchAPI<ScrapeJob>(`/jobs/${id}`),
    create: (data: { audience_id: string; output_formats: string[]; max_topics: number }) =>
      fetchAPI<ScrapeJob>("/jobs/", { method: "POST", body: JSON.stringify(data) }),
  },
  topics: {
    list: (params?: string) => fetchAPI<TopicCluster[]>(`/topics/${params ? `?${params}` : ""}`),
    get: (id: number) => fetchAPI<TopicCluster>(`/topics/${id}`),
  },
  ideas: {
    list: (params?: string) => fetchAPI<ContentIdea[]>(`/ideas/${params ? `?${params}` : ""}`),
    get: (id: number) => fetchAPI<ContentIdea>(`/ideas/${id}`),
    update: (id: number, data: Partial<ContentIdea>) =>
      fetchAPI<ContentIdea>(`/ideas/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  },
};
