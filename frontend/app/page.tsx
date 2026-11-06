"use client";
import { useEffect, useState } from "react";
import Advisor, { Msg } from "@/components/Advisor";
import Kyc from "@/components/Kyc";
import QuoteBill from "@/components/QuoteBill";
import Tracker from "@/components/Tracker";
import UnderTheHood from "@/components/UnderTheHood";
import { Bundle, ChatOut, Item, KycResult, Order, post, Profile } from "@/lib/api";
import { LANGUAGES } from "@/lib/languages";

const STEPS = ["Find your plan", "Your bill", "Verify business", "Track order"];

export default function Home() {
  const [step, setStep] = useState(0);
  const [language, setLanguage] = useState("English");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [profile, setProfile] = useState<Profile>({});
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [modelSaw, setModelSaw] = useState("");
  const [items, setItems] = useState<Item[]>([]);
  const [contract, setContract] = useState(12);
  const [kyc, setKyc] = useState<KycResult | null>(null);
  const [orderId, setOrderId] = useState<string | null>(null);
  const [hood, setHood] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [step]);

  function onReply(out: ChatOut) {
    setSessionId(out.session_id);
    setProfile(out.profile);
    setModelSaw(out.model_saw);
    if (out.bundle && out.bundle !== bundle) {
      setBundle(out.bundle);
      setItems(out.bundle.items);
      setContract(out.bundle.quote.contract_months);
    }
  }

  async function placeOrder(businessName: string) {
    try {
      const o = await post<Order>("/orders", { items, contract_months: contract, business_name: businessName, kyc_status: "verified" });
      setOrderId(o.id);
      setStep(3);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const reachable = [true, !!bundle, !!bundle, !!orderId];
  const hoodPanel = <UnderTheHood profile={profile} bundle={bundle} modelSaw={modelSaw} kyc={kyc} />;

  return (
    <div className="mx-auto flex min-h-dvh max-w-5xl gap-8 lg:px-6 lg:py-6">
      <main className="flex min-h-dvh w-full flex-col bg-paper lg:min-h-0 lg:max-w-[460px] lg:rounded-3xl lg:border lg:border-line">
        <header className="sticky top-0 z-10 border-b border-line bg-paper/95 px-4 pt-3 backdrop-blur lg:rounded-t-3xl">
          <div className="flex items-center justify-between gap-2">
            <p className="whitespace-nowrap font-display text-xl font-bold text-red sm:text-2xl">Airtel Business</p>
            <div className="flex items-center gap-2">
              <label htmlFor="lang" className="sr-only">Language</label>
              <select id="lang" value={language} onChange={(e) => setLanguage(e.target.value)} disabled={messages.length > 0}
                title={messages.length > 0 ? "Language is fixed once the chat starts" : "Choose your language"}
                className="rounded-lg border border-line bg-paper px-2 py-1.5 text-sm">
                {LANGUAGES.map((l) => <option key={l.name} value={l.name}>{l.native}</option>)}
              </select>
              <button onClick={() => setHood(!hood)} aria-expanded={hood}
                className="whitespace-nowrap rounded-lg border border-line px-2 py-1.5 text-sm lg:hidden">
                How it works
              </button>
            </div>
          </div>
          <nav aria-label="Steps" className="mt-3 grid grid-cols-4 gap-1">
            {STEPS.map((s, i) => (
              <button key={s} onClick={() => reachable[i] && setStep(i)} disabled={!reachable[i]}
                aria-current={step === i ? "step" : undefined}
                className={`border-b-[3px] pb-2 text-left text-xs leading-tight ${step === i
                  ? "border-red font-semibold text-ink" : reachable[i] ? "border-ink/30 text-ink" : "border-line text-slate"}`}>
                <span className="block text-[11px] text-slate">{i + 1}</span>{s}
              </button>
            ))}
          </nav>
        </header>

        {hood && <div className="border-b border-line bg-wash p-4 lg:hidden">{hoodPanel}</div>}
        {error && <p role="alert" className="m-4 rounded-lg bg-red/10 px-3 py-2 text-sm text-red-deep">{error}</p>}

        <div className={step === 0 ? "flex min-h-0 flex-1 flex-col lg:h-[70dvh]" : "hidden"}>
          <Advisor language={language} messages={messages} setMessages={setMessages} sessionId={sessionId}
            onReply={onReply} bundle={bundle} onContinue={() => setStep(1)} />
        </div>
        {step === 1 && bundle && (
          <QuoteBill bundle={bundle} businessName={String(profile.business_type ?? "")} items={items} setItems={setItems}
            contract={contract} setContract={setContract} onQuote={() => {}} onContinue={() => setStep(2)} />
        )}
        {step === 2 && <Kyc onResult={setKyc} onVerified={placeOrder} />}
        {step === 3 && orderId && <Tracker orderId={orderId} />}
      </main>

      <aside className="hidden w-full max-w-sm shrink-0 lg:block">
        <h2 className="mb-3 font-display text-xl font-bold">Under the hood</h2>
        {hoodPanel}
        <p className="mt-8 text-xs text-slate">Prototype for Airtel Sync 2026 by Team Shenron, IIITD. All business data is synthetic.</p>
      </aside>
    </div>
  );
}
