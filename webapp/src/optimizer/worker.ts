/// <reference lib="webworker" />
import { optimize } from "./optimize";
import type { OptimizeRequest, WorkerMsg } from "./types";

// Roda a otimizacao fora da thread principal para nao travar a UI.
self.onmessage = (e: MessageEvent<OptimizeRequest>) => {
  const post = (m: WorkerMsg) => (self as DedicatedWorkerGlobalScope).postMessage(m);
  try {
    const result = optimize(e.data, (phase, frac) =>
      post({ type: "progress", phase, frac })
    );
    post({ type: "done", result });
  } catch (err) {
    post({ type: "error", message: err instanceof Error ? err.message : String(err) });
  }
};
