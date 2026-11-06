import { Bundle, KycResult, Profile } from "@/lib/api";

const NAMES: Record<string, string> = {
  segment: "Segment", business_type: "Business", employees: "Employees", sites: "Sites", city: "City",
  city_tier: "City tier", has_gstin: "Has GSTIN", gstin_masked: "GSTIN (verified)", current_internet: "Internet today", needs: "Needs",
};

export default function UnderTheHood({ profile, bundle, modelSaw, kyc }:
  { profile: Profile; bundle: Bundle | null; modelSaw: string; kyc: KycResult | null }) {
  const fields = Object.entries(profile).filter(([k]) => NAMES[k]);
  return (
    <div className="space-y-6 text-sm">
      <p className="text-slate">What the advisor agent is doing, step by step. Prices and eligibility always come from rules, never from the language model.</p>

      <section>
        <h3 className="mb-2 font-semibold">1. Profile extracted from the chat</h3>
        {fields.length === 0 ? <p className="text-slate">Nothing yet. Start chatting.</p> : (
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
            {fields.map(([k, v]) => (
              <div key={k} className="contents"><dt className="text-slate">{NAMES[k]}</dt><dd>{String(v)}</dd></div>
            ))}
          </dl>
        )}
      </section>

      <section>
        <h3 className="mb-2 font-semibold">2. Privacy: what the language model saw</h3>
        <p className="rounded-lg bg-wash p-2 break-words">{modelSaw || "Your last message, with GSTIN, phone and similar numbers replaced by tokens."}</p>
      </section>

      {bundle && (
        <>
          <section>
            <h3 className="mb-2 font-semibold">3. ML ranking: likely fit for this business</h3>
            <ul className="space-y-1">
              {Object.entries(bundle.scores ?? {}).map(([id, s]) => (
                <li key={id} className="flex items-center gap-2">
                  <span className="w-9 text-slate">{id}</span>
                  <span className="h-2 flex-1 rounded bg-wash"><span className="block h-2 rounded bg-red" style={{ width: `${s * 100}%` }} /></span>
                  <span className="w-9 text-right tabular-nums">{Math.round(s * 100)}</span>
                </li>
              ))}
            </ul>
            <p className="mt-1 text-slate">Trained on 5,000 past leads: what similar businesses asked for and kept.</p>
          </section>
          <section>
            <h3 className="mb-2 font-semibold">4. Rules applied</h3>
            {Object.keys(bundle.blocked).length === 0 ? <p className="text-slate">No requested product was blocked.</p> : (
              <ul className="list-disc space-y-1 pl-4">{Object.values(bundle.blocked).map((b) => <li key={b}>{b}</li>)}</ul>
            )}
            <p className="mt-1 text-slate">Eligibility (city tier, size, GSTIN), dependencies, a 6-product cap and a segment budget.</p>
          </section>
        </>
      )}

      {kyc && (
        <section>
          <h3 className="mb-2 font-semibold">5. KYC checks</h3>
          <ul className="space-y-0.5">
            {kyc.checks.map((c) => (
              <li key={c.id} className={c.severity === "error" ? "text-red-deep" : c.severity === "warning" ? "text-warn" : ""}>
                {c.ok ? "✓" : c.severity === "error" ? "✕" : "!"} {c.id.replaceAll("_", " ")}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
