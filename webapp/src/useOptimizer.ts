import { useCallback, useEffect, useRef, useState } from "react";
import type {
  OptimizeRequest,
  OptimizeResult,
  ProgressPhase,
  WorkerMsg,
} from "./optimizer/types";

interface Progress {
  phase: ProgressPhase;
  frac: number;
}

interface State {
  running: boolean;
  progress: Progress | null;
  result: OptimizeResult | null;
  error: string | null;
}

const PHASE_LABEL: Record<ProgressPhase, string> = {
  pool: "Gerando candidatos",
  greedy: "Selecionando por cobertura",
  sa: "Refinando (annealing)",
  montecarlo: "Simulando sorteios",
};

export function phaseLabel(p: ProgressPhase): string {
  return PHASE_LABEL[p];
}

export function useOptimizer() {
  const workerRef = useRef<Worker | null>(null);
  const [state, setState] = useState<State>({
    running: false,
    progress: null,
    result: null,
    error: null,
  });

  // Cria (e recria) o worker. Encerrado ao desmontar.
  const spawn = useCallback(() => {
    workerRef.current?.terminate();
    const w = new Worker(new URL("./optimizer/worker.ts", import.meta.url), {
      type: "module",
    });
    w.onmessage = (e: MessageEvent<WorkerMsg>) => {
      // Uma mensagem "done"/"progress" pode ja estar na fila do event loop
      // quando o usuario troca de loteria (reset()/spawn() de um worker novo)
      // no meio do calculo. Sem essa checagem, o resultado antigo (de outra
      // loteria) sobrescreve o estado limpo/novo -- e a carteira errada
      // aparece na tela.
      if (workerRef.current !== w) return;
      const m = e.data;
      if (m.type === "progress")
        setState((s) => ({ ...s, progress: { phase: m.phase, frac: m.frac } }));
      else if (m.type === "done")
        setState({ running: false, progress: null, result: m.result, error: null });
      else if (m.type === "error")
        setState({ running: false, progress: null, result: null, error: m.message });
    };
    workerRef.current = w;
    return w;
  }, []);

  useEffect(() => () => workerRef.current?.terminate(), []);

  const run = useCallback(
    (req: OptimizeRequest) => {
      const w = spawn();
      setState({ running: true, progress: { phase: "pool", frac: 0 }, result: null, error: null });
      w.postMessage(req);
    },
    [spawn]
  );

  const reset = useCallback(() => {
    workerRef.current?.terminate();
    workerRef.current = null;
    setState({ running: false, progress: null, result: null, error: null });
  }, []);

  return { ...state, run, reset };
}
