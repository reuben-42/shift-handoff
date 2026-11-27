import { DemoBanner } from "./components/DemoBanner";

export function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <DemoBanner />
      <main className="mx-auto max-w-5xl p-6">
        <h1 className="text-2xl font-semibold">Shift Handoff Copilot</h1>
        <p className="mt-2 text-slate-600">Skeleton. The unit board arrives in step 09.</p>
      </main>
    </div>
  );
}
