"use client";
import { useEffect, useState } from "react";
import { get } from "@/lib/api";

type Lead = {
  lead_id: string; business: string; type: string; city: string; language: string; source: string;
  dropped_at: string; reason: string; contact: string; score: number; next_action: string;
};

export default function Partner() {
  const [leads, setLeads] = useState<Lead[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { get<Lead[]>("/partner/leads").then(setLeads).catch((e) => setError(e.message)); }, []);

  return (
    <main className="mx-auto max-w-5xl px-4 py-6">
      <p className="font-display text-2xl font-bold text-red">Airtel Business</p>
      <h1 className="font-display text-3xl font-bold">Leads worth a call today</h1>
      <p className="max-w-2xl text-slate">
        Businesses that left before getting a quote, ranked by how likely they are to sign up if contacted.
        The digital journey handles simple cases; field sales and local partners take these.
      </p>
      {error && <p role="alert" className="mt-4 text-red-deep">{error}</p>}
      {!leads && !error && <p className="mt-4 text-slate">Loading leads…</p>}
      {leads && (
        <div className="mt-5 overflow-x-auto rounded-2xl border border-line bg-paper">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-line text-slate">
              <tr>
                <th className="px-3 py-2 font-medium">Chance</th>
                <th className="px-3 py-2 font-medium">Business</th>
                <th className="px-3 py-2 font-medium">Contact</th>
                <th className="px-3 py-2 font-medium">Why they left</th>
                <th className="px-3 py-2 font-medium">Suggested next step</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {leads.map((l) => (
                <tr key={l.lead_id}>
                  <td className="px-3 py-2">
                    <span className="flex items-center gap-2">
                      <span className="h-2 w-16 rounded bg-wash"><span className="block h-2 rounded bg-red" style={{ width: `${l.score * 100}%` }} /></span>
                      <span className="tabular-nums">{Math.round(l.score * 100)}</span>
                    </span>
                  </td>
                  <td className="px-3 py-2"><p className="font-medium">{l.business}</p><p className="text-slate">{l.type}, {l.city}</p></td>
                  <td className="px-3 py-2"><p>{l.contact}</p><p className="text-slate">Speaks {l.language}</p></td>
                  <td className="px-3 py-2"><p>{l.reason}</p><p className="text-slate">At: {l.dropped_at}, via {l.source.toLowerCase()}</p></td>
                  <td className="px-3 py-2">{l.next_action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
