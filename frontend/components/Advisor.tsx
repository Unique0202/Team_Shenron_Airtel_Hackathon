"use client";
import { useEffect, useRef, useState } from "react";
import { Bundle, ChatOut, inr, post } from "@/lib/api";
import { LANGUAGES } from "@/lib/languages";

export type Msg = { role: "owner" | "advisor"; text: string };

const EXAMPLES = [
  "I run a pharmacy in Pune with 4 staff",
  "We have 2 dental clinics in Kochi, 12 people",
  "मेरी लखनऊ में किराना दुकान है, GST नहीं है",
  "Restaurant chain, 5 outlets in Bengaluru, 60 staff",
];

type Props = {
  language: string;
  messages: Msg[];
  setMessages: (f: (m: Msg[]) => Msg[]) => void;
  sessionId: string | null;
  onReply: (out: ChatOut) => void;
  bundle: Bundle | null;
  onContinue: () => void;
};

export default function Advisor({ language, messages, setMessages, sessionId, onReply, bundle, onContinue }: Props) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [listening, setListening] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  const lang = LANGUAGES.find((l) => l.name === language) ?? LANGUAGES[0];

  useEffect(() => end.current?.scrollIntoView({ behavior: "smooth", block: "end" }), [messages, busy]);

  async function send(msg: string) {
    if (!msg.trim() || busy) return;
    setText("");
    setError("");
    setMessages((m) => [...m, { role: "owner", text: msg }]);
    setBusy(true);
    try {
      const out = await post<ChatOut>("/chat", { session_id: sessionId, message: msg, language });
      setMessages((m) => [...m, { role: "advisor", text: out.reply }]);
      onReply(out);
    } catch (e) {
      setError(`${(e as Error).message}. Your message was not lost; tap send to try again.`);
      setMessages((m) => m.slice(0, -1));
      setText(msg);
    } finally {
      setBusy(false);
    }
  }

  function listen() {
    // browser speech recognition: no extra service, works in Chrome on Android
    const W = window as unknown as { SpeechRecognition?: new () => SpeechRec; webkitSpeechRecognition?: new () => SpeechRec };
    const SR = W.SpeechRecognition ?? W.webkitSpeechRecognition;
    if (!SR) return setError("Voice input is not supported in this browser. Please type instead.");
    const r = new SR();
    r.lang = lang.speech;
    r.onresult = (e) => send(e.results[0][0].transcript);
    r.onend = () => setListening(false);
    setListening(true);
    r.start();
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4" aria-live="polite">
        <Bubble role="advisor" text={lang.greeting} />
        {messages.map((m, i) => <Bubble key={i} {...m} />)}
        {busy && <p className="pl-1 text-sm text-slate">Udyam Mitra is typing…</p>}
        {bundle && !busy && (
          <div className="rounded-2xl border border-red/20 bg-paper p-4">
            <p className="font-display text-lg font-semibold leading-tight">Your plan is ready</p>
            <p className="mt-1 text-sm text-slate">
              {bundle.quote.lines.length} services for {inr(bundle.quote.monthly_total)} a month
            </p>
            <button onClick={onContinue}
              className="mt-3 w-full rounded-xl bg-red py-3 font-semibold text-white hover:bg-red-deep">
              See your bill
            </button>
          </div>
        )}
        {messages.length === 0 && (
          <div className="pt-2">
            <p className="mb-2 text-sm text-slate">Or start with an example:</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map((e) => (
                <button key={e} onClick={() => send(e)}
                  className="rounded-full border border-line bg-paper px-3 py-1.5 text-left text-sm hover:border-red">
                  {e}
                </button>
              ))}
            </div>
          </div>
        )}
        <div ref={end} />
      </div>
      {error && <p role="alert" className="mx-4 mb-2 rounded-lg bg-red/10 px-3 py-2 text-sm text-red-deep">{error}</p>}
      <form onSubmit={(e) => { e.preventDefault(); send(text); }}
        className="flex items-center gap-2 border-t border-line bg-paper p-3">
        <label htmlFor="msg" className="sr-only">Message</label>
        <input id="msg" value={text} onChange={(e) => setText(e.target.value)} autoComplete="off"
          placeholder="Type about your business…"
          className="min-w-0 flex-1 rounded-xl border border-line bg-wash px-3 py-3 outline-none focus:border-red" />
        <button type="button" onClick={listen} aria-label={`Speak in ${lang.name}`}
          className={`grid size-12 place-items-center rounded-xl border ${listening ? "border-red bg-red text-white" : "border-line"}`}>
          <MicIcon />
        </button>
        <button type="submit" disabled={busy || !text.trim()}
          className="h-12 rounded-xl bg-ink px-4 font-semibold text-white disabled:opacity-40">
          Send
        </button>
      </form>
    </div>
  );
}

function Bubble({ role, text }: Msg) {
  const mine = role === "owner";
  return (
    <div className={`flex ${mine ? "justify-end" : "justify-start"}`}>
      <p className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 leading-relaxed ${
        mine ? "rounded-br-sm bg-ink text-white" : "rounded-bl-sm border border-line bg-paper"}`}>
        {text.replace(/\*\*/g, "")}
      </p>
    </div>
  );
}

function MicIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" strokeLinecap="round" />
    </svg>
  );
}

type SpeechRec = {
  lang: string;
  start: () => void;
  onresult: (e: { results: { [i: number]: { [j: number]: { transcript: string } } } }) => void;
  onend: () => void;
};
