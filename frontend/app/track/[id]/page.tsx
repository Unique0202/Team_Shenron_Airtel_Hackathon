import { Suspense } from "react";
import Tracker from "@/components/Tracker";

async function Order({ params }: { params: PageProps<"/track/[id]">["params"] }) {
  const { id } = await params;
  return <Tracker orderId={id} />;
}

export default function TrackPage({ params }: PageProps<"/track/[id]">) {
  return (
    <main className="mx-auto min-h-dvh max-w-[460px] bg-paper">
      <header className="border-b border-line px-4 py-3">
        <p className="font-display text-2xl font-bold text-red">Airtel Business</p>
      </header>
      <Suspense fallback={<p className="px-4 py-6 text-slate">Loading your order…</p>}>
        <Order params={params} />
      </Suspense>
    </main>
  );
}
