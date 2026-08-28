import { useState } from "react";
import type { OptimizeResult } from "../optimizer/types";
import { getLottery, precoBilhete } from "../lotteries";
import { brl, dd, pct, umEm } from "../format";

interface Props {
  result: OptimizeResult;
  fixed: Set<number>;
}

function buildText(result: OptimizeResult, custoTotal: number): string {
  const lot = getLottery(result.lotteryId);
  const label = (n: number) => dd(n - (lot.numberOffset ?? 0));
  const linhas = result.bilhetes.map(
    (b, i) => `Bilhete ${String(i + 1).padStart(2, "0")}: ${b.map(label).join(" - ")}`
  );
  return (
    `${lot.nome} — ${result.bilhetes.length} bilhetes (${result.bilhetes[0].length} dezenas cada)\n` +
    `Custo total: ${brl(custoTotal)}\n\n` +
    linhas.join("\n") +
    "\n"
  );
}

function buildCsv(result: OptimizeResult): string {
  const lot = getLottery(result.lotteryId);
  const offset = lot.numberOffset ?? 0;
  const pick = result.bilhetes[0].length;
  const header = ["bilhete", ...Array.from({ length: pick }, (_, i) => `d${i + 1}`)];
  const rows = result.bilhetes.map((b, i) => [i + 1, ...b.map((d) => d - offset)].join(","));
  return header.join(",") + "\n" + rows.join("\n") + "\n";
}

function download(name: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ResultView({ result, fixed }: Props) {
  const lot = getLottery(result.lotteryId);
  const numLabel = (n: number) => dd(n - (lot.numberOffset ?? 0));
  const [copied, setCopied] = useState(false);

  // Custo recalculado com o preco atual (pode ter vindo de override remoto).
  const pick = result.bilhetes[0].length;
  const precoUnit = precoBilhete(lot, pick);
  const custoTotal = precoUnit * result.bilhetes.length;

  const eficiencia =
    result.overlapTotal > 0 ? result.overlapTeorico / result.overlapTotal : 1;

  // Quao mais provavel ganhar com a carteira do que com um unico jogo.
  const multiplicador = result.pSingle > 0 ? result.pAtLeastOne / result.pSingle : 1;
  const multStr =
    multiplicador.toLocaleString("pt-BR", {
      maximumFractionDigits: multiplicador < 10 ? 1 : 0,
    }) + "×";

  // Vantagem sobre a MESMA quantidade de jogos escolhidos no chute (aleatorios/
  // por uma pessoa) -- e a vantagem real que a otimizacao traz.
  const n = result.bilhetes.length;
  const edge =
    result.pRefIndep > 0 ? Math.max(0, result.pAtLeastOne / result.pRefIndep - 1) : 0;
  const edgeStr = "+" + pct(edge, edge < 0.1 ? 1 : 0);

  const copy = async () => {
    await navigator.clipboard.writeText(buildText(result, custoTotal));
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  return (
    <section className="result">
      <div className="cost-banner" style={{ borderColor: lot.cor }}>
        <div>
          <span className="cost-label">Custo total da carteira</span>
          <span className="cost-value" style={{ color: lot.cor }}>
            {brl(custoTotal)}
          </span>
        </div>
        <div className="cost-detail">
          {result.bilhetes.length} bilhetes × {brl(precoUnit)}
        </div>
      </div>

      <div className="metrics">
        <Metric
          titulo={`Chance de algum prêmio (≥ ${result.limiar} acertos)`}
          valor={umEm(result.pAtLeastOne)}
          sub={`${pct(result.pAtLeastOne)} de chance em algum dos ${result.bilhetes.length} bilhetes`}
          destaque={lot.cor}
        />
        <Metric
          titulo="Mais chances de ganhar"
          valor={multStr}
          sub="mais provável que apostar um jogo só"
          destaque={lot.cor}
        />
        <Metric
          titulo="Vantagem sobre o chute"
          valor={edgeStr}
          sub={`de chance a mais que ${n} ${n === 1 ? "jogo escolhido" : "jogos escolhidos"} no chute`}
          destaque={lot.cor}
        />
        <Metric
          titulo="Dezenas diferentes na carteira"
          valor={`${result.cobertura} de ${result.universe}`}
          sub="quanto mais espalhadas, melhor o aproveitamento dos jogos"
        />
      </div>

      <div className="actions">
        <button type="button" className="btn-secondary" onClick={copy}>
          {copied ? "✓ Copiado!" : "Copiar bilhetes"}
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => download(`${lot.id}-bilhetes.txt`, buildText(result, custoTotal), "text/plain")}
        >
          Baixar .txt
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => download(`${lot.id}-bilhetes.csv`, buildCsv(result), "text/csv")}
        >
          Baixar .csv
        </button>
      </div>

      <ol className="tickets">
        {result.bilhetes.map((b, i) => (
          <li key={i} className={`ticket ${i < result.userCount ? "is-user" : ""}`}>
            <span className="ticket-n">
              {dd(i + 1)}
              {i < result.userCount && (
                <span className="ticket-tag" style={{ background: lot.cor }}>
                  sua
                </span>
              )}
            </span>
            <div className="ticket-balls">
              {b.map((d) => (
                <span
                  key={d}
                  className={`tball ${fixed.has(d) ? "is-fixed" : ""}`}
                  style={{
                    background: lot.cor,
                    borderColor: lot.cor,
                  }}
                  title={fixed.has(d) ? "dezena fixada por você" : undefined}
                >
                  {numLabel(d)}
                </span>
              ))}
            </div>
          </li>
        ))}
      </ol>

      <details className="tech">
        <summary>Detalhes técnicos</summary>
        <p>
          Os jogos são escolhidos para ficarem o mais <em>independentes</em> possível
          entre si — espalhando as dezenas para que, quando um bilhete não acerta, outro
          tenha mais chance de acertar. Isso é feito por um otimizador de cobertura
          combinatória (seleção gulosa + recozimento simulado) que minimiza a sobreposição
          total entre os bilhetes.
        </p>
        <ul>
          <li>
            Sobreposição total da carteira: <strong>{result.overlapTotal}</strong> (ótimo
            teórico Ω* = {result.overlapTeorico}; eficiência {pct(eficiencia, 0)})
          </li>
          <li>
            Sobreposição média: {result.overlapMedio.toFixed(1)} dezenas em comum por par
            de bilhetes
          </li>
          <li>
            P(≥ {result.limiar}) estimada por simulação de {(60000).toLocaleString("pt-BR")}{" "}
            sorteios; chance de um bilhete isolado: {pct(result.pSingle, 3)}
          </li>
        </ul>
      </details>
    </section>
  );
}

function Metric({
  titulo,
  valor,
  sub,
  destaque,
}: {
  titulo: string;
  valor: string;
  sub: string;
  destaque?: string;
}) {
  return (
    <div className="metric">
      <span className="metric-titulo">{titulo}</span>
      <span className="metric-valor" style={destaque ? { color: destaque } : undefined}>
        {valor}
      </span>
      <span className="metric-sub">{sub}</span>
    </div>
  );
}
