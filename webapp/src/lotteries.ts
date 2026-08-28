/**
 * Configuracao das loterias suportadas.
 *
 * O metodo de otimizacao (minimizar sobreposicao entre bilhetes) vale para
 * qualquer loteria do tipo "escolha k dezenas de um universo de v; ganha quem
 * acertar >= t das d dezenas sorteadas". Para adicionar uma nova loteria, basta
 * incluir uma entrada aqui.
 *
 * PRECOS: valores vigentes apos o reajuste das Loterias CAIXA de 09/07/2025.
 * Nao existe API oficial de precos -- a API publica da CAIXA so retorna
 * resultados de sorteios. Por isso os precos sao constantes datadas. Para
 * atualizar SEM republicar o site, hospede um arquivo `prices.json` ao lado do
 * app (ver applyRemotePrices abaixo); senao, basta editar `basePrice` aqui.
 */

/** Quando os precos abaixo foram conferidos pela ultima vez. */
export let PRICES_DATE = "jul/2025";

export interface Lottery {
  id: string;
  nome: string;
  cor: string;
  /** Universo de dezenas: 1..universe */
  universe: number;
  /** Quantidade de dezenas sorteadas */
  draw: number;
  /** Minimo de dezenas que o apostador marca (= aposta simples) */
  minPick: number;
  /** Maximo de dezenas que o apostador pode marcar num unico bilhete */
  maxPick: number;
  /** Acertos minimos para ganhar algum premio (limiar t) */
  premioMin: number;
  /** Preco da aposta simples (minPick dezenas), em reais */
  basePrice: number;
  /** Faixas de premiacao, da menor para a maior (para exibir) */
  faixas: number[];
  /** Sorteios independentes por concurso; ganha acertando o limiar em
   *  qualquer um deles (ex.: Dupla Sena = 2). Default 1. */
  draws?: number;
  /** Deslocamento de exibicao: dezena mostrada = dezena interna - offset.
   *  Usado pela Lotomania, cujo volante vai de 00 a 99 (interno 1..100). */
  numberOffset?: number;
  /** Nota sobre alguma faixa de premiacao real que a otimizacao NAO
   *  considera (ex.: acertar zero na Lotomania, mes da sorte no Dia de
   *  Sorte). Exibida como aviso quando presente. */
  notaPremiacao?: string;
}

export const LOTTERIES: Lottery[] = [
  {
    id: "lotofacil",
    nome: "Lotofácil",
    cor: "#930989",
    universe: 25,
    draw: 15,
    minPick: 15,
    maxPick: 20,
    premioMin: 11,
    basePrice: 3.5,
    faixas: [11, 12, 13, 14, 15],
  },
  {
    id: "megasena",
    nome: "Mega-Sena",
    cor: "#209869",
    universe: 60,
    draw: 6,
    minPick: 6,
    maxPick: 20,
    premioMin: 4,
    basePrice: 6.0,
    faixas: [4, 5, 6],
  },
  {
    id: "quina",
    nome: "Quina",
    cor: "#260085",
    universe: 80,
    draw: 5,
    minPick: 5,
    maxPick: 15,
    premioMin: 2,
    basePrice: 3.0,
    faixas: [2, 3, 4, 5],
  },
  {
    id: "lotomania",
    nome: "Lotomania",
    cor: "#f58220",
    universe: 100,
    draw: 20,
    minPick: 50,
    maxPick: 50,
    premioMin: 15,
    basePrice: 3.0,
    faixas: [15, 16, 17, 18, 19, 20],
    numberOffset: 1,
    notaPremiacao:
      "Também há prêmio para quem não acerta nenhuma das 20 dezenas sorteadas; essa faixa não entra na otimização nem nas chances mostradas.",
  },
  {
    id: "duplasena",
    nome: "Dupla Sena",
    cor: "#a61c6c",
    universe: 50,
    draw: 6,
    minPick: 6,
    maxPick: 15,
    premioMin: 3,
    basePrice: 3.0,
    faixas: [3, 4, 5, 6],
    draws: 2,
  },
  {
    id: "diadesorte",
    nome: "Dia de Sorte",
    cor: "#cb9a1e",
    universe: 31,
    draw: 7,
    minPick: 7,
    maxPick: 15,
    premioMin: 4,
    basePrice: 2.5,
    faixas: [4, 5, 6, 7],
    notaPremiacao:
      "Cada bilhete também sorteia um Mês da Sorte com prêmio próprio; essa faixa não entra na otimização nem nas chances mostradas.",
  },
];

export function getLottery(id: string): Lottery {
  const l = LOTTERIES.find((x) => x.id === id);
  if (!l) throw new Error(`Loteria desconhecida: ${id}`);
  return l;
}

/**
 * Dezena "oficial" a exibir para o usuario (aplica o numberOffset). Uso
 * interno segue sempre 1..universe; so a exibicao muda (ex.: Lotomania
 * guarda 1..100 mas mostra 00..99).
 */
export function displayNum(lot: Lottery, n: number): number {
  return n - (lot.numberOffset ?? 0);
}

/** C(n, k) com inteiros (suficiente para os tamanhos aqui). */
export function comb(n: number, k: number): number {
  if (k < 0 || k > n) return 0;
  k = Math.min(k, n - k);
  let r = 1;
  for (let i = 0; i < k; i++) r = (r * (n - i)) / (i + 1);
  return Math.round(r);
}

/**
 * Preco de um bilhete que marca `pick` dezenas: o bilhete equivale a C(pick,
 * minPick) apostas simples, logo custa basePrice * C(pick, minPick).
 */
export function precoBilhete(lot: Lottery, pick: number): number {
  return lot.basePrice * comb(pick, lot.minPick);
}

/**
 * Override opcional de precos sem republicar o site. Se existir um `prices.json`
 * servido junto do app, no formato:
 *   { "_date": "set/2026", "lotofacil": 4.0, "megasena": 7.0, "quina": 3.5 }
 * os valores presentes substituem `basePrice` das loterias correspondentes.
 * Falha em silencio (sem arquivo / offline / formato invalido) -> usa os
 * valores embutidos.
 */
export async function applyRemotePrices(): Promise<boolean> {
  try {
    const resp = await fetch("./prices.json", { cache: "no-store" });
    if (!resp.ok) return false;
    const data = (await resp.json()) as Record<string, unknown>;
    let changed = false;
    for (const lot of LOTTERIES) {
      const v = data[lot.id];
      if (typeof v === "number" && v > 0) {
        lot.basePrice = v;
        changed = true;
      }
    }
    if (typeof data._date === "string") {
      PRICES_DATE = data._date;
      changed = true;
    }
    return changed;
  } catch {
    return false;
  }
}
