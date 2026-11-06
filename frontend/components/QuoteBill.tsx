"use client";
import { useEffect, useState } from "react";
import { Bundle, inr, Item, post, Quote } from "@/lib/api";

const PRIMARY = ["P01", "P02", "P03", "P04", "P05", "P06"];

type Props = {
  bundle: Bundle;
  businessName: string;
  items: Item[];
  setItems: (i: Item[]) => void;
  contract: number;
  setContract: (c: number) => void;
  onQuote: (q: Quote) => void;
  onContinue: () => void;
};

export default function QuoteBill({ bundle, businessName, items, setItems, contract, setContract, onQuote, onContinue }: Props) {
  const [quote, setQuote] = useState<Quote>(bundle.quote);
  const [error, setError] = useState("");

  useEffect(() => {
    post<Quote>("/quote", { items, contract_months: contract })
      .then((q) => { setQuote(q); onQuote(q); setError(""); })
      .catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items, contract]);

  const has = (id: string) => items.some((i) => i.id === id);
  const toggle = (it: Item) => setItems(has(it.id) ? items.filter((i) => i.id !== it.id) : [...items, { id: it.id, qty: it.qty }]);
  const setQty = (id: string, qty: number) => setItems(items.map((i) => (i.id === id ? { ...i, qty: Math.max(1, Math.min(50, qty)) } : i)));
  const optional = [
    ...bundle.items.filter((i) => !PRIMARY.includes(i.id)).map((i) => ({ ...i, name: quote.lines.find((l) => l.id === i.id)?.name ?? i.id, inBundle: true })),
    ...bundle.addons.map((a) => ({ ...a, inBundle: false })),
  ];

  return (
    <div className="space-y-5 px-4 py-5">
      <fieldset>
        <legend className="mb-2 font-medium">How long do you want the plan?</legend>
        <div className="grid grid-cols-3 gap-2" role="radiogroup">
          {[12, 24, 36].map((c) => (
            <button key={c} role="radio" aria-checked={quote.contract_months === c} onClick={() => setContract(c)}
              className={`rounded-xl border py-2.5 text-center ${quote.contract_months === c
                ? "border-ink bg-ink text-white" : "border-line bg-paper"}`}>
              <span className="block font-semibold">{c / 12} {c === 12 ? "year" : "years"}</span>
              <span className="block text-xs opacity-80">{c === 12 ? "Standard price" : c === 24 ? "Lower price, half setup" : "Lowest price, free setup"}</span>
            </button>
          ))}
        </div>
        {quote.contract_months > contract && (
          <p className="mt-2 text-sm text-slate">Some services in your plan need at least {quote.contract_months / 12} years.</p>
        )}
      </fieldset>

      <section aria-label="Your bill" className="bill print-in bg-paper px-5 py-7 shadow-[0_1px_0_#e3e6eb]">
        <div className="flex items-baseline justify-between">
          <p className="font-display text-xl font-bold text-red">Airtel Business</p>
          <p className="text-sm text-slate">Monthly estimate</p>
        </div>
        {businessName && <p className="text-sm text-slate">For {businessName}</p>}
        <ul className="mt-4 space-y-3">
          {quote.lines.map((l) => (
            <li key={l.id}>
              <div className="flex items-end">
                <span className="font-medium">{l.name}</span>
                <span className="leader" aria-hidden />
                <span className="tabular-nums">{inr(l.monthly)}</span>
              </div>
              <p className="text-sm text-slate">
                {l.qty} × {inr(l.unit_price)} {l.unit}
                {bundle.reasons[l.id] ? `. ${cap(bundle.reasons[l.id])}` : ""}
              </p>
            </li>
          ))}
        </ul>
        <div className="mt-5 border-t-2 border-dashed border-line pt-4">
          <div className="flex items-end justify-between">
            <span className="font-medium">You pay every month</span>
            <span className="font-display text-4xl font-bold tabular-nums leading-none">{inr(quote.monthly_total)}</span>
          </div>
          <p className="mt-1 text-right text-sm text-slate">plus GST, one bill for everything</p>
          <div className="mt-3 flex justify-between text-sm">
            <span>One-time setup</span>
            <span className="tabular-nums">
              {quote.setup_saved > 0 && <s className="mr-2 text-slate">{inr(quote.setup_total + quote.setup_saved)}</s>}
              {inr(quote.setup_total)}
            </span>
          </div>
          <div className="mt-1 flex justify-between text-sm">
            <span>Everything working in</span>
            <span>{quote.ready_in_days} {quote.ready_in_days === 1 ? "day" : "days"}</span>
          </div>
        </div>
      </section>

      {error && <p role="alert" className="rounded-lg bg-red/10 px-3 py-2 text-sm text-red-deep">{error}</p>}

      <section>
        <h2 className="mb-2 font-medium">Add or remove services</h2>
        <ul className="divide-y divide-line rounded-2xl border border-line bg-paper">
          {optional.map((o) => (
            <li key={o.id} className="flex items-center gap-3 px-4 py-3">
              <label className="flex flex-1 items-center gap-3">
                <input type="checkbox" checked={has(o.id)} onChange={() => toggle(o)} className="size-5 accent-red" />
                <span>{o.name}</span>
              </label>
              {has(o.id) && (
                <span className="flex items-center gap-1" aria-label={`Quantity of ${o.name}`}>
                  <button onClick={() => setQty(o.id, (items.find((i) => i.id === o.id)?.qty ?? 1) - 1)}
                    className="size-8 rounded-lg border border-line" aria-label="One less">−</button>
                  <span className="w-6 text-center tabular-nums">{items.find((i) => i.id === o.id)?.qty}</span>
                  <button onClick={() => setQty(o.id, (items.find((i) => i.id === o.id)?.qty ?? 1) + 1)}
                    className="size-8 rounded-lg border border-line" aria-label="One more">+</button>
                </span>
              )}
            </li>
          ))}
        </ul>
        {Object.keys(bundle.blocked).length > 0 && (
          <p className="mt-3 text-sm text-slate">Not included: {Object.values(bundle.blocked).join("; ")}.</p>
        )}
      </section>

      <button onClick={onContinue} disabled={!!error}
        className="w-full rounded-xl bg-red py-3.5 font-semibold text-white hover:bg-red-deep disabled:opacity-40">
        Continue to business verification
      </button>
    </div>
  );
}

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
