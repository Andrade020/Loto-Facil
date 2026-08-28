export interface OptimizeRequest {
  lotteryId: string;
  /** Quantos bilhetes gerar */
  nBilhetes: number;
  /** Dezenas marcadas por bilhete (>= minPick da loteria) */
  pick: number;
  /** Dezenas obrigatorias (entram em todos os bilhetes gerados) */
  fixed: number[];
  /** Dezenas proibidas (nunca aparecem nos bilhetes gerados) */
  excluded: number[];
  /** Apostas completas do proprio usuario; entram na carteira e os bilhetes
   *  gerados sao escolhidos para combinar melhor com elas. Cada uma tem `pick`
   *  dezenas. */
  seedTickets: number[][];
  /** Sorteios Monte Carlo para estimar P(>= limiar) */
  numSim: number;
  /** Refinar com Simulated Annealing (minimiza sobreposicao) */
  refine: boolean;
  /** Semente para reprodutibilidade (opcional) */
  seed?: number;
}

export interface OptimizeResult {
  lotteryId: string;
  bilhetes: number[][];
  /** Quantos dos primeiros bilhetes sao apostas do proprio usuario */
  userCount: number;
  /** Limiar de premiacao usado (t) */
  limiar: number;
  /** P(>= t acertos) de um unico bilhete, exata (hipergeometrica) */
  pSingle: number;
  /** P(>= t em ao menos um bilhete) estimada por Monte Carlo */
  pAtLeastOne: number;
  /** Limite superior teorico: 1 - (1 - pSingle)^n (bilhetes independentes) */
  pRefIndep: number;
  /** Dezenas distintas cobertas pela carteira */
  cobertura: number;
  universe: number;
  /** Sobreposicao total Sum_{i<j} |Ai cap Aj| da carteira */
  overlapTotal: number;
  /** Sobreposicao minima teorica dadas as restricoes (Omega*) */
  overlapTeorico: number;
  /** Sobreposicao media por par */
  overlapMedio: number;
  /** Custo por bilhete (R$) */
  precoBilhete: number;
  /** Custo total da carteira (R$) */
  custoTotal: number;
  warnings: string[];
}

export type ProgressPhase = "pool" | "greedy" | "sa" | "montecarlo";

export interface ProgressMsg {
  type: "progress";
  phase: ProgressPhase;
  frac: number;
}
export interface DoneMsg {
  type: "done";
  result: OptimizeResult;
}
export interface ErrorMsg {
  type: "error";
  message: string;
}
export type WorkerMsg = ProgressMsg | DoneMsg | ErrorMsg;
