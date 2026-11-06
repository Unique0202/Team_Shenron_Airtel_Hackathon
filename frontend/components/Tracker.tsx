"use client";
import { useEffect, useState } from "react";
import { get, inr, Order, post } from "@/lib/api";

const fmt = (d: string) => new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short" });

export default function Tracker({ orderId }: { orderId: string }) {
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    get<Order>(`/orders/${orderId}`).then(setOrder).catch((e) => setError(e.message));
  }, [orderId]);

  if (error) return <p className="px-4 py-6 text-red-deep">{error}. Check the order number in your SMS.</p>;
  if (!order) return <p className="px-4 py-6 text-slate">Loading your order…</p>;
  const current = order.timeline.filter((t) => t.done).length;

  return (
    <div className="space-y-5 px-4 py-5">
      <div>
        <p className="text-sm text-slate">Order {order.id}{order.business_name ? ` for ${order.business_name}` : ""}</p>
        <h2 className="font-display text-3xl font-bold leading-tight">{order.status}</h2>
        <p className="text-slate">
          {current < order.timeline.length
            ? `Everything working by ${fmt(order.timeline.at(-1)!.expected)}. We send you a WhatsApp message at every step, so there is no need to call.`
            : "All your services are live."}
        </p>
      </div>

      <ol className="relative ml-2 border-l-2 border-line">
        {order.timeline.map((t, i) => (
          <li key={t.step} className="relative pb-5 pl-6 last:pb-0">
            <span aria-hidden className={`absolute -left-[9px] top-1 size-4 rounded-full border-2 ${
              t.done ? "border-ok bg-ok" : i === current ? "border-red bg-paper" : "border-line bg-paper"}`} />
            <p className={`font-medium ${t.done ? "" : "text-slate"}`}>
              {t.step}<span className="sr-only">{t.done ? " (done)" : i === current ? " (next)" : ""}</span>
            </p>
            <p className="text-sm text-slate">{t.done ? "Done" : `Expected ${fmt(t.expected)}`}</p>
          </li>
        ))}
      </ol>

      <section className="rounded-2xl border border-line bg-paper p-4">
        <h3 className="mb-2 font-medium">Your services</h3>
        <ul className="space-y-1.5 text-[15px]">
          {order.lines.map((l) => (
            <li key={l.name} className="flex justify-between gap-2">
              <span>{l.qty} × {l.name}</span>
              <span className="text-slate">ready {fmt(l.ready_by)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 border-t border-line pt-3 text-sm">
          {inr(order.quote.monthly_total)} a month on one bill, {order.quote.contract_months / 12}-year plan
        </p>
      </section>

      {current < order.timeline.length && (
        <button onClick={() => post<Order>(`/orders/${order.id}/advance`, {}).then(setOrder)}
          className="w-full rounded-xl border border-dashed border-slate py-3 text-sm text-slate">
          Demo: mark the next step done
        </button>
      )}
    </div>
  );
}
