"use client";
import { useState } from "react";
import { get, KycResult, post, upload } from "@/lib/api";

const DOCS: [string, string, string][] = [
  ["gst_certificate", "GST certificate", "Proves your business is registered for GST"],
  ["udyam_certificate", "Udyam certificate", "Proves you are a registered small business"],
  ["signatory_id", "ID of the person signing", "The owner, partner or director who signs"],
  ["address_proof", "Electricity bill", "From the last 3 months, for the installation address"],
];
const SAMPLES = Array.from({ length: 12 }, (_, i) => `K${String(i + 1).padStart(2, "0")}`);

type Fields = Record<string, string | boolean>;
type Registry = {
  found: boolean; error?: string; gstin?: string; trade_name?: string; constitution?: string; state?: string; status?: string;
};

export default function Kyc({ onVerified, onResult }: { onVerified: (name: string) => void; onResult: (r: KycResult) => void }) {
  const [consent, setConsent] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [gstin, setGstin] = useState("");
  const [reg, setReg] = useState<Registry | null>(null);
  const [docs, setDocs] = useState<Record<string, Fields | null>>({});
  const [reading, setReading] = useState<string[]>([]);
  const [result, setResult] = useState<KycResult | null>(null);
  const [error, setError] = useState("");

  async function read(file: Blob, name: string, slot: string) {
    setReading((r) => [...r, slot]);
    try {
      const out = await upload<{ doc_type: string; fields: Fields }>("/kyc/extract", file, name);
      const type = DOCS.some(([t]) => t === out.doc_type) ? out.doc_type : slot;
      setDocs((d) => ({ ...d, [type]: out.fields }));
      setResult(null);
    } catch (e) {
      setError(`Could not read ${name}: ${(e as Error).message}`);
    } finally {
      setReading((r) => r.filter((s) => s !== slot));
    }
  }

  async function loadSample(k: string) {
    setDocs({});
    setResult(null);
    setError("");
    await Promise.all(DOCS.map(async ([t]) => {
      const r = await fetch(`/samples/${k}_${t}.png`);
      if (r.ok) await read(await r.blob(), `${k}_${t}.png`, t);
    }));
  }

  async function verify() {
    setError("");
    try {
      const res = await post<KycResult>("/kyc/validate", { docs: Object.fromEntries(DOCS.map(([t]) => [t, docs[t] ?? null])) });
      setResult(res);
      onResult(res);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (!consent) {
    return (
      <div className="space-y-4 px-4 py-5">
        <h2 className="font-display text-2xl font-bold leading-tight">Before we verify your business</h2>
        <div className="space-y-3 rounded-2xl border border-line bg-paper p-4 text-[15px] leading-relaxed">
          <p><b>What we collect:</b> your GSTIN, Udyam number, one ID of the person signing, and one electricity bill. Nothing else.</p>
          <p><b>Why:</b> telecom rules require us to verify every business connection. We use these details only to verify you and set up your services.</p>
          <p><b>How we protect it:</b> numbers are hidden on screen and in our records, and are never shared with our assistant in readable form.</p>
          <p><b>How long we keep it:</b> photos are read and deleted immediately. We keep only the verification result, for as long as telecom rules require.</p>
          <p><b>Your choice:</b> you can withdraw consent any time from the order page. Your services would then be stopped.</p>
        </div>
        <label className="flex items-start gap-3">
          <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} className="mt-1 size-5 accent-red" />
          <span>I agree to share these documents with Airtel Business for verifying my business.</span>
        </label>
        <button disabled={!agreed} onClick={() => setConsent(true)}
          className="w-full rounded-xl bg-red py-3.5 font-semibold text-white disabled:opacity-40">
          Agree and continue
        </button>
      </div>
    );
  }

  const failures = result?.checks.filter((c) => c.severity !== "ok") ?? [];
  const passed = result?.checks.filter((c) => c.ok).length ?? 0;

  return (
    <div className="space-y-5 px-4 py-5">
      <section>
        <h2 className="mb-1 font-medium">Your GSTIN</h2>
        <p className="mb-2 text-sm text-slate">We fetch your details from the GST registry, so you don&apos;t have to type them.</p>
        <form className="flex gap-2" onSubmit={async (e) => {
          e.preventDefault();
          setReg(await get<Registry>(`/lookup/gstin/${encodeURIComponent(gstin.trim())}`).catch((x) => ({ found: false, error: x.message })));
        }}>
          <label htmlFor="gstin" className="sr-only">GSTIN</label>
          <input id="gstin" value={gstin} onChange={(e) => setGstin(e.target.value.toUpperCase())} maxLength={15}
            placeholder="15-character GSTIN" autoComplete="off"
            className="min-w-0 flex-1 rounded-xl border border-line bg-paper px-3 py-3 font-medium tracking-wide outline-none focus:border-red" />
          <button className="rounded-xl bg-ink px-4 font-semibold text-white">Fetch</button>
        </form>
        {reg && (reg.found ? (
          <div className="mt-2 rounded-xl border border-line bg-paper p-3 text-sm">
            <p className="font-medium">{reg.trade_name}</p>
            <p className="text-slate">{reg.constitution}, {reg.state}. GSTIN {reg.gstin}</p>
            <p className={reg.status === "Active" ? "text-ok" : "font-medium text-red-deep"}>Registration {reg.status?.toLowerCase()}</p>
          </div>
        ) : <p className="mt-2 text-sm text-red-deep">{reg.error}</p>)}
      </section>

      <section>
        <div className="mb-2 flex items-baseline justify-between gap-2">
          <h2 className="font-medium">Your documents</h2>
          <label className="text-sm text-slate">
            Demo:{" "}
            <select onChange={(e) => e.target.value && loadSample(e.target.value)} defaultValue=""
              className="rounded-lg border border-line bg-paper px-2 py-1">
              <option value="">Use a sample applicant</option>
              {SAMPLES.map((k) => <option key={k}>{k}</option>)}
            </select>
          </label>
        </div>
        <ul className="divide-y divide-line rounded-2xl border border-line bg-paper">
          {DOCS.map(([t, label, hint]) => {
            const f = docs[t];
            return (
              <li key={t} className="flex items-center gap-3 px-4 py-3">
                <div className="flex-1">
                  <p className="font-medium">{label}</p>
                  <p className="text-sm text-slate">
                    {reading.includes(t) ? "Reading…" : f ? (f._unreadable ? "Too blurred to read. Please retake the photo." : summary(t, f)) : hint}
                  </p>
                </div>
                <label className="cursor-pointer rounded-lg border border-line px-3 py-2 text-sm font-medium hover:border-red">
                  {f ? "Replace" : "Add photo"}
                  <input type="file" accept="image/*,application/pdf" capture="environment" className="sr-only"
                    onChange={(e) => e.target.files?.[0] && read(e.target.files[0], e.target.files[0].name, t)} />
                </label>
              </li>
            );
          })}
        </ul>
      </section>

      {error && <p role="alert" className="rounded-lg bg-red/10 px-3 py-2 text-sm text-red-deep">{error}</p>}

      {!result && (
        <button onClick={verify} disabled={reading.length > 0 || Object.keys(docs).length === 0}
          className="w-full rounded-xl bg-ink py-3.5 font-semibold text-white disabled:opacity-40">
          Verify my business
        </button>
      )}

      {result && (
        <section aria-live="polite" className="rounded-2xl border border-line bg-paper p-4">
          <p className={`font-display text-xl font-bold ${result.status === "verified" ? "text-ok" : "text-red-deep"}`}>
            {result.status === "verified" ? "Business verified" : "A few things need fixing"}
          </p>
          <p className="text-sm text-slate">{passed} of {result.checks.length} checks passed</p>
          {failures.length > 0 && (
            <ul className="mt-3 space-y-2">
              {failures.map((c) => (
                <li key={c.id} className="flex gap-2 text-[15px]">
                  <span aria-hidden className={c.severity === "error" ? "text-red" : "text-warn"}>{c.severity === "error" ? "✕" : "!"}</span>
                  <span><span className="sr-only">{c.severity}: </span>{c.message}</span>
                </li>
              ))}
            </ul>
          )}
          {result.status === "verified" ? (
            <button onClick={() => onVerified(String(docs.gst_certificate?.["Trade name"] ?? reg?.trade_name ?? ""))}
              className="mt-4 w-full rounded-xl bg-red py-3.5 font-semibold text-white hover:bg-red-deep">
              E-sign and place order
            </button>
          ) : (
            <p className="mt-3 text-sm text-slate">Fix the items above and upload again, or ask for a callback and our local partner will help you.</p>
          )}
        </section>
      )}
    </div>
  );
}

function summary(t: string, f: Fields) {
  const pick = { gst_certificate: "Trade name", udyam_certificate: "Enterprise name", signatory_id: "Name", address_proof: "Bill date" }[t]!;
  return `Read: ${f[pick] || "details found"}`;
}
