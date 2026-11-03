export type Count = { label: string; count: number };
export type AdminUser = {
  id: number; name: string | null; phone_number: string; city: string | null;
  preferred_language: string; created_at: string; premium_expires_at: string | null;
  plan_tier: string; setup_step: string | null; stage: string;
  total_queries: number; used_today: number; last_active: string | null; connected_apps: number;
};
export type UserDetail = AdminUser & {
  interests: string[]; usage: { date: string; query_count: number }[];
  connections: { toolkit: string; status: string; updated_at: string }[];
  actions: { toolkit: string; tool_slug: string; status: string; created_at: string }[];
  events: { intent: string; emotion: string | null; created_at: string }[];
};
export type Overview = {
  total_users: number; today_queries: number; active_today: number; new_users_24h: number;
  stages: { stage: string; count: number }[]; flows_24h: Record<string, number>;
  success_percent: number | null; generated_at: string;
};
export type Analytics = {
  days: number; daily: { date: string; queries: number; active_users: number }[];
  intents: Count[]; emotions: Count[]; connectors: Count[]; tools: Count[];
  models: { model: string; route: string; status: string; calls: number; latency_ms: number; input_tokens: number | null; output_tokens: number | null }[];
  telemetry_note: string;
};
export type ConfigValues = {
  reply_model: string; fast_model: string; json_model: string;
  FREE_DAILY_LIMIT: number; PAID_DAILY_LIMIT: number; MAX_DAILY_LIMIT: number;
  SIGNUP_PREVIEW_MESSAGES: number; ADS_ENABLED: boolean;
};
export type Config = { revision: number; values: ConfigValues; updated_at: string | null };
export type Audit = { id: number; action: string; changes: Record<string, { before: unknown; after: unknown }>; created_at: string };
export type Flow = { id: number; direction: string; sender: string | null; status: string; has_error: boolean; created_at: string };
export type Integrations = { environment: string; services: Record<string, boolean>; configured_toolkits: string[]; note: string };
export type Campaign = { id: number; brand_name: string; category: string; impressions: number; clicks: number; is_active: boolean; budget_paise: number; spent_paise: number };

export async function adminApi<T>(key: string, path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("X-Admin-Key", key);
  headers.set("Content-Type", "application/json");
  const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || ""}${path}`, { ...init, headers, cache: "no-store" });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(response.status === 403 ? "Access denied. Check your admin key." :
      typeof body.detail === "string" ? body.detail : `Request failed (${response.status}). Please retry.`);
  }
  return body;
}
