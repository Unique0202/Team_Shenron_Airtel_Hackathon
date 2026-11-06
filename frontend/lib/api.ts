// trailing slashes stripped: "https://x.onrender.com/" + "/chat" would 404
export const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

async function handle<T>(r: Response): Promise<T> {
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail ?? `Request failed (${r.status})`);
  return j as T;
}

export const get = <T,>(path: string) => fetch(API + path).then((r) => handle<T>(r));

export const post = <T,>(path: string, body: unknown) =>
  fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((r) => handle<T>(r));

export const upload = <T,>(path: string, file: Blob, name: string) => {
  const fd = new FormData();
  fd.append("file", file, name);
  return fetch(API + path, { method: "POST", body: fd }).then((r) => handle<T>(r));
};

export type Item = { id: string; qty: number };
export type Line = {
  id: string; name: string; description: string; unit: string; qty: number;
  unit_price: number; monthly: number; setup: number; setup_list: number; install_days: number;
};
export type Quote = {
  contract_months: number; lines: Line[]; monthly_total: number; setup_total: number;
  setup_saved: number; ready_in_days: number;
};
export type Bundle = {
  items: Item[]; addons: (Item & { name: string })[]; reasons: Record<string, string>;
  blocked: Record<string, string>; quote: Quote; scores?: { id: string; name: string; score: number }[];
};
export type Profile = Record<string, string | number | boolean>;
export type ChatOut = { session_id: string; reply: string; model_saw: string; profile: Profile; bundle: Bundle | null };
export type Check = { id: string; ok: boolean; severity: "ok" | "warning" | "error"; message: string };
export type KycResult = {
  status: "verified" | "action_needed"; checks: Check[];
  registry: { gstin: Record<string, string> | null; udyam: Record<string, string> | null };
};
export type Order = {
  id: string; business_name: string; created: string; status: string; quote: Quote;
  timeline: { step: string; expected: string; done: boolean }[];
  lines: { name: string; qty: number; ready_by: string }[];
};

export const inr = (n: number) => "₹" + Math.round(n).toLocaleString("en-IN");
