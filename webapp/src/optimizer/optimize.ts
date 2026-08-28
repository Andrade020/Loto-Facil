/**
 * Otimizador de carteiras de apostas -- porte TypeScript de lotofacil_optimizer.py,
 * generalizado para qualquer loteria do tipo (v, k, d, t) e com suporte a dezenas
 * fixas/excluidas.
 *
 * Pipeline:
 *   1. Gera um pool de bilhetes candidatos aleatorios distintos.
 *   2. Selecao gulosa por cobertura maxima (Greedy Max-Coverage, Nemhauser 1978).
 *   3. Refino por Simulated Annealing minimizando a sobreposicao total
 *      Sum_{i<j} |Ai cap Aj| -- menos sobreposicao => eventos mais independentes
 *      => maior P(>= t acertos em ao menos um bilhete).
 *   4. Estimativa Monte Carlo de P(>= t) e metricas de qualidade.
 *
 * Toda a otimizacao roda no "espaco livre" (dezenas permitidas menos as fixas),
 * em indices 0..vf-1; as dezenas fixas sao reanexadas no final.
 */

import { comb, getLottery, precoBilhete } from "../lotteries";
import type { OptimizeRequest, OptimizeResult, ProgressPhase } from "./types";

// ---------------------------------------------------------------------------
// RNG semeavel (mulberry32) -- deterministico dado um seed
// ---------------------------------------------------------------------------
function makeRng(seed: number) {
  let a = seed >>> 0;
  return function next(): number {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

type Rng = () => number;
const randint = (rng: Rng, n: number) => Math.floor(rng() * n);

// ---------------------------------------------------------------------------
// Geracao de bilhetes distintos no espaco livre (indices 0..vf-1)
// ---------------------------------------------------------------------------
function sampleTicket(rng: Rng, scratch: Int32Array, kFree: number): number[] {
  // Fisher-Yates parcial: seleciona kFree indices distintos de 0..vf-1.
  const vf = scratch.length;
  for (let i = 0; i < kFree; i++) {
    const j = i + randint(rng, vf - i);
    const tmp = scratch[i];
    scratch[i] = scratch[j];
    scratch[j] = tmp;
  }
  const out = new Array<number>(kFree);
  for (let i = 0; i < kFree; i++) out[i] = scratch[i];
  out.sort((x, y) => x - y);
  return out;
}

function generateDistinctTickets(
  rng: Rng,
  vf: number,
  kFree: number,
  count: number
): number[][] {
  const scratch = new Int32Array(vf);
  for (let i = 0; i < vf; i++) scratch[i] = i;

  const seen = new Set<string>();
  const tickets: number[][] = [];
  const maxAttempts = count * 50 + 100;
  let attempts = 0;
  while (tickets.length < count && attempts < maxAttempts) {
    attempts++;
    const t = sampleTicket(rng, scratch, kFree);
    const key = t.join(",");
    if (seen.has(key)) continue;
    seen.add(key);
    tickets.push(t);
  }
  return tickets;
}

// ---------------------------------------------------------------------------
// Selecao gulosa por cobertura maxima
// ---------------------------------------------------------------------------
function greedyCoverageSelect(
  pool: number[][],
  n: number,
  vf: number,
  kFree: number,
  seedColCount: Int32Array
): number[][] {
  const M = pool.length;
  const covered = new Uint8Array(vf);
  const available = new Uint8Array(M).fill(1);
  const cumulativeOverlap = new Float64Array(M);
  const MULT = n * kFree + 1;
  const bestSet = new Uint8Array(vf);

  // Linha de base: dezenas ja cobertas pelas apostas do usuario e a
  // sobreposicao de cada candidato com elas.
  for (let k = 0; k < vf; k++) if (seedColCount[k] > 0) covered[k] = 1;
  for (let i = 0; i < M; i++) {
    let ov = 0;
    const members = pool[i];
    for (let m = 0; m < members.length; m++) ov += seedColCount[members[m]];
    cumulativeOverlap[i] = ov;
  }

  const selected: number[][] = [];
  for (let step = 0; step < n; step++) {
    let best = -1;
    let bestScore = -Infinity;
    for (let i = 0; i < M; i++) {
      if (!available[i]) continue;
      const members = pool[i];
      let gain = 0;
      for (let m = 0; m < members.length; m++) if (!covered[members[m]]) gain++;
      const score = gain * MULT - cumulativeOverlap[i];
      if (score > bestScore) {
        bestScore = score;
        best = i;
      }
    }
    if (best < 0) break;

    const bestMembers = pool[best];
    selected.push(bestMembers);
    available[best] = 0;
    bestSet.fill(0);
    for (let m = 0; m < bestMembers.length; m++) {
      covered[bestMembers[m]] = 1;
      bestSet[bestMembers[m]] = 1;
    }
    // Atualiza overlap acumulado de cada candidato com o bilhete recem-escolhido.
    for (let i = 0; i < M; i++) {
      if (!available[i]) continue;
      const members = pool[i];
      let ov = 0;
      for (let m = 0; m < members.length; m++) if (bestSet[members[m]]) ov++;
      cumulativeOverlap[i] += ov;
    }
  }
  return selected;
}

// ---------------------------------------------------------------------------
// Refino por Simulated Annealing (minimiza sobreposicao total)
// ---------------------------------------------------------------------------
function refineOverlapSA(
  tickets: number[][],
  vf: number,
  rng: Rng,
  nIter: number,
  seedColCount: Int32Array,
  onProgress?: (frac: number) => void
): number[][] {
  const n = tickets.length;
  const kFree = tickets[0].length;
  if (kFree === 0 || kFree === vf || (n < 2 && seedColCount.every((c) => c === 0)))
    return tickets;

  // Estado: membros por bilhete + indicador booleano + contagem por coluna.
  // A contagem inicia com a pegada das apostas do usuario (seedColCount), de
  // modo que minimizar a sobreposicao tambem afaste os bilhetes gerados delas.
  const members = tickets.map((t) => t.slice());
  const tBool: Uint8Array[] = members.map((t) => {
    const b = new Uint8Array(vf);
    for (const x of t) b[x] = 1;
    return b;
  });
  const colCount = new Int32Array(seedColCount);
  for (const t of members) for (const x of t) colCount[x]++;

  // Omega = Sum_k C(colCount[k], 2)
  let omega = 0;
  for (let k = 0; k < vf; k++) omega += (colCount[k] * (colCount[k] - 1)) / 2;

  let best = members.map((t) => t.slice());
  let bestOmega = omega;

  const T0 = 2.0;
  const cooling = 0.9993;
  let T = T0;
  const progStep = Math.max(1, Math.floor(nIter / 50));

  for (let it = 0; it < nIter; it++) {
    const ti = randint(rng, n);
    const tk = members[ti];
    const b = tBool[ti];

    const rem = tk[randint(rng, kFree)];
    let add = randint(rng, vf);
    while (b[add]) add = randint(rng, vf); // sorteia um indice fora do bilhete

    // delta = colCount[add] - colCount[rem] + 1  (deducao em omega_star_insight)
    const delta = colCount[add] - colCount[rem] + 1;

    if (delta < 0 || rng() < Math.exp(-delta / T)) {
      // aplica a troca
      const idx = tk.indexOf(rem);
      tk[idx] = add;
      b[rem] = 0;
      b[add] = 1;
      colCount[rem]--;
      colCount[add]++;
      omega += delta;
      if (omega < bestOmega) {
        bestOmega = omega;
        best = members.map((t) => t.slice());
      }
    }
    T *= cooling;
    if (onProgress && it % progStep === 0) onProgress(it / nIter);
  }
  return best;
}

// ---------------------------------------------------------------------------
// Monte Carlo: P(>= t acertos em ao menos um bilhete)
// Sorteios vem do UNIVERSO COMPLETO da loteria (1..v), como na vida real.
// ---------------------------------------------------------------------------
function montecarloPAtLeastOne(
  bilhetes: number[][], // dezenas reais 1..v
  universe: number,
  draw: number,
  limiar: number,
  numSim: number,
  rng: Rng,
  drawsPerConcurso: number,
  onProgress?: (frac: number) => void
): number {
  const n = bilhetes.length;
  // membros como indices 0..v-1
  const memb = bilhetes.map((b) => b.map((x) => x - 1));
  const drawBool = new Uint8Array(universe);
  const scratch = new Int32Array(universe);
  for (let i = 0; i < universe; i++) scratch[i] = i;

  let acertos = 0;
  const progStep = Math.max(1, Math.floor(numSim / 50));
  const chosen = new Int32Array(draw);

  for (let s = 0; s < numSim; s++) {
    let won = false;
    // Loterias com mais de um sorteio por concurso (ex.: Dupla Sena) ganham
    // acertando o limiar em QUALQUER um dos sorteios independentes.
    for (let rodada = 0; rodada < drawsPerConcurso && !won; rodada++) {
      // Fisher-Yates parcial: sorteia `draw` dezenas do universo completo.
      for (let i = 0; i < draw; i++) {
        const j = i + randint(rng, universe - i);
        const tmp = scratch[i];
        scratch[i] = scratch[j];
        scratch[j] = tmp;
        chosen[i] = scratch[i];
        drawBool[scratch[i]] = 1;
      }
      // algum bilhete com >= limiar acertos?
      for (let i = 0; i < n; i++) {
        const m = memb[i];
        let hits = 0;
        for (let k = 0; k < m.length; k++) {
          if (drawBool[m[k]]) {
            hits++;
            if (hits >= limiar) {
              won = true;
              break;
            }
          }
        }
        if (won) break;
      }
      // limpa apenas as posicoes marcadas
      for (let i = 0; i < draw; i++) drawBool[chosen[i]] = 0;
    }
    if (won) acertos++;
    if (onProgress && s % progStep === 0) onProgress(s / numSim);
  }
  return acertos / numSim;
}

// ---------------------------------------------------------------------------
// P exata de um unico bilhete (distribuicao hipergeometrica)
// ---------------------------------------------------------------------------
function pSingleTicket(
  universe: number,
  draw: number,
  pick: number,
  limiar: number
): number {
  const total = comb(universe, draw);
  let p = 0;
  const maxHits = Math.min(pick, draw);
  for (let a = limiar; a <= maxHits; a++) {
    p += (comb(pick, a) * comb(universe - pick, draw - a)) / total;
  }
  return p;
}

// ---------------------------------------------------------------------------
// Omega* -- sobreposicao minima teorica do espaco livre
// ---------------------------------------------------------------------------
function omegaStarFree(n: number, kFree: number, vf: number): number {
  if (vf === 0 || kFree === 0) return 0;
  const total = n * kFree;
  const q = Math.floor(total / vf);
  const r = total - q * vf;
  return r * comb(q + 1, 2) + (vf - r) * comb(q, 2);
}

// ---------------------------------------------------------------------------
// Orquestrador
// ---------------------------------------------------------------------------
export function optimize(
  req: OptimizeRequest,
  onProgress?: (phase: ProgressPhase, frac: number) => void
): OptimizeResult {
  const lot = getLottery(req.lotteryId);
  const warnings: string[] = [];

  const v = lot.universe;
  const pick = req.pick;
  const n = req.nBilhetes;

  // Validacao basica
  if (n < 1) throw new Error("Numero de bilhetes deve ser >= 1.");
  if (pick < lot.minPick || pick > lot.maxPick)
    throw new Error(
      `Marque entre ${lot.minPick} e ${lot.maxPick} dezenas na ${lot.nome}.`
    );

  const fixed = [...new Set(req.fixed)].filter((x) => x >= 1 && x <= v);
  const excludedSet = new Set(
    req.excluded.filter((x) => x >= 1 && x <= v && !fixed.includes(x))
  );

  // Dezenas permitidas = universo - excluidas
  const allowed: number[] = [];
  for (let d = 1; d <= v; d++) if (!excludedSet.has(d)) allowed.push(d);

  if (fixed.length > pick)
    throw new Error(
      `Voce fixou ${fixed.length} dezenas, mais que as ${pick} marcadas por bilhete.`
    );
  if (allowed.length < pick)
    throw new Error(
      `Sobram apenas ${allowed.length} dezenas permitidas, menos que as ${pick} por bilhete. Exclua menos dezenas.`
    );

  // Espaco livre: dezenas permitidas que nao sao fixas
  const fixedSet = new Set(fixed);
  const freeNums = allowed.filter((d) => !fixedSet.has(d));
  const vf = freeNums.length;
  const kFree = pick - fixed.length;

  if (kFree > vf)
    throw new Error(
      `Nao ha dezenas livres suficientes (${vf}) para completar ${kFree} por bilhete.`
    );

  // Apostas do proprio usuario (sementes): completas, entram na carteira como
  // estao. Sao saneadas (distintas, dentro do universo, com `pick` dezenas).
  const seedTickets: number[][] = (req.seedTickets ?? [])
    .map((t) => [...new Set(t)].filter((x) => x >= 1 && x <= v).sort((a, b) => a - b))
    .filter((t) => t.length === pick);
  const nUser = seedTickets.length;
  const nAuto = Math.max(0, n - nUser);
  const total = nUser + nAuto;

  // Pegada das sementes no espaco livre (baseline do objetivo de sobreposicao)
  const freeIndexOf = new Map<number, number>();
  freeNums.forEach((d, i) => freeIndexOf.set(d, i));
  const seedColCount = new Int32Array(vf);
  for (const t of seedTickets)
    for (const d of t) {
      const idx = freeIndexOf.get(d);
      if (idx !== undefined) seedColCount[idx]++;
    }

  // Quantidade maxima de bilhetes distintos possiveis (para os gerados)
  const maxDistinct = comb(vf, kFree);
  if (nAuto > 0 && kFree === 0) {
    warnings.push(
      "Voce fixou todas as dezenas do bilhete: os bilhetes gerados serao iguais e nao ha o que otimizar."
    );
  } else if (nAuto > 0 && maxDistinct < nAuto) {
    warnings.push(
      `So existem ${maxDistinct} combinacoes distintas possiveis com essas restricoes; alguns bilhetes gerados se repetirao.`
    );
  }

  const seed = req.seed ?? (Math.random() * 2 ** 32) >>> 0;
  const rng = makeRng(seed);

  // 1) Pool (apenas para os bilhetes que serao GERADOS)
  onProgress?.("pool", 0);
  const nPool = Math.min(Math.max(500, nAuto * 60), Math.max(nAuto, maxDistinct));
  const pool =
    nAuto === 0
      ? []
      : kFree === 0
        ? Array.from({ length: nAuto }, () => [] as number[])
        : generateDistinctTickets(rng, vf, kFree, nPool);
  onProgress?.("pool", 1);

  // 2) Greedy
  onProgress?.("greedy", 0);
  let selectedFree: number[][] =
    nAuto === 0
      ? []
      : kFree === 0
        ? Array.from({ length: nAuto }, () => [] as number[])
        : greedyCoverageSelect(pool, nAuto, vf, kFree, seedColCount);
  // Se o pool nao tinha bilhetes distintos suficientes, completa repetindo.
  while (selectedFree.length < nAuto && pool.length > 0) {
    selectedFree.push(pool[selectedFree.length % pool.length]);
  }
  onProgress?.("greedy", 1);

  // 3) SA
  if (req.refine && nAuto > 0 && kFree > 0 && kFree < vf) {
    const nIter = Math.max(8000, nAuto * kFree * 250);
    selectedFree = refineOverlapSA(selectedFree, vf, rng, nIter, seedColCount, (f) =>
      onProgress?.("sa", f)
    );
  }
  onProgress?.("sa", 1);

  // Converte indices livres -> dezenas reais e reanexa as fixas
  const autoBilhetes: number[][] = selectedFree.map((t) => {
    const dezenas = t.map((idx) => freeNums[idx]).concat(fixed);
    dezenas.sort((a, b) => a - b);
    return dezenas;
  });

  // Carteira final: apostas do usuario primeiro, depois as geradas.
  const bilhetes: number[][] = [...seedTickets, ...autoBilhetes];

  const drawsPerConcurso = lot.draws ?? 1;

  // 4) Monte Carlo
  onProgress?.("montecarlo", 0);
  const pAtLeastOne = montecarloPAtLeastOne(
    bilhetes,
    v,
    lot.draw,
    lot.premioMin,
    req.numSim,
    rng,
    drawsPerConcurso,
    (f) => onProgress?.("montecarlo", f)
  );
  onProgress?.("montecarlo", 1);

  // Metricas. Com mais de um sorteio por concurso (ex.: Dupla Sena), a chance
  // de UM bilhete e a de acertar o limiar em qualquer um dos sorteios
  // independentes: 1 - (1 - p_1_sorteio)^drawsPerConcurso.
  const pSingleUmSorteio = pSingleTicket(v, lot.draw, pick, lot.premioMin);
  const pSingle = 1 - Math.pow(1 - pSingleUmSorteio, drawsPerConcurso);
  const pRefIndep = 1 - Math.pow(1 - pSingle, total);

  // Sobreposicao real sobre os bilhetes completos
  const colCountFull = new Int32Array(v + 1);
  for (const b of bilhetes) for (const d of b) colCountFull[d]++;
  let overlapTotal = 0;
  let cobertura = 0;
  for (let d = 1; d <= v; d++) {
    const c = colCountFull[d];
    overlapTotal += (c * (c - 1)) / 2;
    if (c > 0) cobertura++;
  }
  const pares = comb(total, 2);
  const overlapMedio = pares > 0 ? overlapTotal / pares : 0;
  const overlapTeorico = fixed.length * comb(total, 2) + omegaStarFree(total, kFree, vf);

  const preco = precoBilhete(lot, pick);

  return {
    lotteryId: lot.id,
    bilhetes,
    userCount: nUser,
    limiar: lot.premioMin,
    pSingle,
    pAtLeastOne,
    pRefIndep,
    cobertura,
    universe: v,
    overlapTotal,
    overlapTeorico,
    overlapMedio,
    precoBilhete: preco,
    custoTotal: preco * total,
    warnings,
  };
}
