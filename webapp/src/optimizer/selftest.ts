/**
 * Self-test do otimizador (sem navegador): `npm test`.
 * Valida que a otimizacao melhora P(>= t) frente a bilhetes aleatorios e que a
 * sobreposicao se aproxima do otimo teorico Omega*.
 */
import { optimize } from "./optimize";
import type { OptimizeRequest } from "./types";
import { getLottery } from "../lotteries";

let failures = 0;
function check(cond: boolean, msg: string) {
  const ok = cond ? "OK " : "FALHOU";
  if (!cond) failures++;
  console.log(`[${ok}] ${msg}`);
}

function run(label: string, req: OptimizeRequest) {
  const r = optimize(req);
  console.log(`\n=== ${label} (${req.lotteryId}, n=${req.nBilhetes}, marca=${req.pick}) ===`);
  console.log(`  bilhetes:`);
  for (const b of r.bilhetes) console.log(`    ${b.join(" ")}`);
  console.log(`  P(>=${r.limiar}) MC ............ ${r.pAtLeastOne.toFixed(5)}`);
  console.log(`  limite independencia ...... ${r.pRefIndep.toFixed(5)}`);
  console.log(`  P 1 bilhete ............... ${r.pSingle.toFixed(6)}`);
  console.log(`  cobertura ................. ${r.cobertura}/${r.universe}`);
  console.log(`  overlap total ............. ${r.overlapTotal} (otimo ${r.overlapTeorico})`);
  console.log(`  custo total ............... R$ ${r.custoTotal.toFixed(2)}`);
  if (r.warnings.length) console.log(`  avisos: ${r.warnings.join(" | ")}`);

  check(r.bilhetes.length === req.nBilhetes, "gerou n bilhetes");
  check(
    r.bilhetes.every((b) => b.length === req.pick),
    "cada bilhete tem `pick` dezenas"
  );
  check(
    r.bilhetes.every((b) => new Set(b).size === b.length),
    "dezenas distintas dentro de cada bilhete"
  );
  check(r.overlapTotal >= r.overlapTeorico, "overlap >= otimo teorico Omega*");
  // A carteira otimizada (anti-correlacionada) iguala ou SUPERA a baseline
  // aleatoria/independente -- nunca piora alem do ruido de Monte Carlo.
  check(
    r.pAtLeastOne >= r.pRefIndep - 0.01,
    "P(MC) >= baseline independencia (otimizacao nao piora)"
  );
  return r;
}

// Lotofacil: SA deve bater perto de Omega* e P(MC) deve superar a de 1 bilhete.
const lf = run("Lotofacil annealing", {
  lotteryId: "lotofacil",
  nBilhetes: 5,
  pick: 15,
  fixed: [],
  excluded: [],
  seedTickets: [],
  numSim: 60000,
  refine: true,
  seed: 42,
});
check(lf.overlapTotal <= lf.overlapTeorico + 5, "overlap proximo do otimo (gap <= 5)");
check(lf.pAtLeastOne > lf.pSingle, "carteira supera 1 bilhete isolado");

// Mega-Sena com dezenas fixas e excluidas
const ms = run("Mega-Sena fixas/excluidas", {
  lotteryId: "megasena",
  nBilhetes: 8,
  pick: 6,
  fixed: [7, 13],
  excluded: [1, 2, 3, 4, 5],
  seedTickets: [],
  numSim: 40000,
  refine: true,
  seed: 7,
});
check(
  ms.bilhetes.every((b) => b.includes(7) && b.includes(13)),
  "todas as fixas presentes em todos os bilhetes"
);
check(
  ms.bilhetes.every((b) => ![1, 2, 3, 4, 5].some((x) => b.includes(x))),
  "nenhuma dezena excluida aparece"
);

// Quina
run("Quina", {
  lotteryId: "quina",
  nBilhetes: 10,
  pick: 5,
  fixed: [],
  excluded: [],
  seedTickets: [],
  numSim: 40000,
  refine: true,
  seed: 99,
});

// Apostas-semente: usuario monta 2 jogos; o otimizador completa ate 5.
const sd = run("Lotofacil com apostas do usuario", {
  lotteryId: "lotofacil",
  nBilhetes: 5,
  pick: 15,
  fixed: [],
  excluded: [],
  seedTickets: [
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
  ],
  numSim: 40000,
  refine: true,
  seed: 3,
});
check(sd.userCount === 2, "userCount = 2 (apostas do usuario contadas)");
check(sd.bilhetes.length === 5, "carteira tem 5 bilhetes (2 do usuario + 3 gerados)");
check(
  sd.bilhetes[0].join(",") === "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15",
  "1a aposta do usuario preservada como dada"
);

// Lotomania: pick fixo (minPick == maxPick == 50), numeracao 00-99 (offset 1).
const lm = run("Lotomania", {
  lotteryId: "lotomania",
  nBilhetes: 4,
  pick: 50,
  fixed: [],
  excluded: [],
  seedTickets: [],
  numSim: 20000,
  refine: true,
  seed: 11,
});
check(
  !lm.warnings.some((w) => w.includes("nenhuma das 20")),
  "Lotomania nao repete a nota de premiacao como warning de execucao (fica so na UI, antes de gerar)"
);
check(
  !!getLottery("lotomania").notaPremiacao?.includes("nenhuma das 20"),
  "Lotomania declara a nota sobre a faixa de acertar zero (nao modelada)"
);

// Dupla Sena: dois sorteios por concurso -- P de 1 bilhete deve refletir as
// duas chances (maior que a de um unico sorteio isolado).
const ds = run("Dupla Sena (2 sorteios)", {
  lotteryId: "duplasena",
  nBilhetes: 6,
  pick: 6,
  fixed: [],
  excluded: [],
  seedTickets: [],
  numSim: 40000,
  refine: true,
  seed: 21,
});
check(ds.pAtLeastOne > ds.pSingle, "Dupla Sena: carteira supera 1 bilhete isolado");

// Dia de Sorte: universo pequeno (31), aviso sobre o Mes da Sorte nao modelado.
const dds = run("Dia de Sorte", {
  lotteryId: "diadesorte",
  nBilhetes: 5,
  pick: 7,
  fixed: [],
  excluded: [],
  seedTickets: [],
  numSim: 20000,
  refine: true,
  seed: 31,
});
check(
  !dds.warnings.some((w) => w.includes("Mês da Sorte")),
  "Dia de Sorte nao repete a nota de premiacao como warning de execucao (fica so na UI, antes de gerar)"
);
check(
  !!getLottery("diadesorte").notaPremiacao?.includes("Mês da Sorte"),
  "Dia de Sorte declara a nota sobre o Mes da Sorte (nao modelado)"
);

console.log(`\n${failures === 0 ? "TODOS OS TESTES PASSARAM" : failures + " TESTE(S) FALHARAM"}`);
if (failures > 0) process.exit(1);
