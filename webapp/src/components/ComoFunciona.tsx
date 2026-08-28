import { useState } from "react";
import type { Route } from "../useHashRoute";

/**
 * Dados REAIS (nao ilustrativos): gerados chamando optimize() de verdade
 * para a Lotofacil, pick=15, 80.000 sorteios Monte Carlo, seed fixa.
 * pAtLeastOne = carteira otimizada (Prisma); pRefIndep = baseline de
 * bilhetes independentes/aleatorios (1-(1-p)^n). Reproduzivel rodando
 * `optimize({ lotteryId: "lotofacil", pick: 15, nBilhetes: n, ... })`.
 */
const CHART = [
  { n: "1", opt: 10.59, rnd: 10.59 },
  { n: "5", opt: 49.14, rnd: 42.86 },
  { n: "10", opt: 76.29, rnd: 67.35 },
  { n: "20", opt: 94.41, rnd: 89.34 },
  { n: "50", opt: 99.91, rnd: 99.63 },
  { n: "100", opt: 100.0, rnd: 100.0 },
];

const MYTH_FACTS = [
  {
    myth: "Aumenta a chance de um bilhete específico ganhar",
    fact: "Cada bilhete sozinho mantém exatamente a mesma chance de sempre",
  },
  {
    myth: "Prevê quais números vão sair no sorteio",
    fact: "Não olha sorteios passados nem prevê nada, só organiza a combinação",
  },
  {
    myth: "Muda o retorno esperado do jogo",
    fact: "O retorno esperado continua negativo, como em qualquer loteria",
  },
  {
    myth: "Funciona igual em qualquer quantidade de bilhetes",
    fact: "A vantagem é maior em quantidades pequenas e some perto de 50-100 bilhetes",
  },
];

export default function ComoFunciona({ navigate }: { navigate: (r: Route) => void }) {
  const [spread, setSpread] = useState(false);

  const A = [1, 4, 7, 10];
  const B = spread ? [2, 5, 8, 11] : [1, 4, 7, 9];
  const covered = new Set([...A, ...B]).size;

  return (
    <div>
      <header className="cf-hero">
        <p className="hero-tag">como funciona</p>
        <h1>Como o Prisma escolhe seus números</h1>
        <p className="subtitle">
          Sem bola de cristal: é um problema de matemática que já existia antes da loteria, e
          o Prisma resolve isso pra sua carteira de bilhetes.
        </p>
      </header>

      <section className="cf-band">
        <div className="cf-inner">
          <p className="cf-label">01 · o problema</p>
          <h2 className="cf-title">Bilhetes parecidos desperdiçam dinheiro</h2>
          <p className="cf-body">
            Se duas apostas marcam quase os mesmos números, elas competem pelo mesmo
            resultado: quando uma perde, a outra também perde. Espalhar os números faz cada
            bilhete cobrir um pedaço diferente do sorteio.
          </p>
          <div className="cf-toggle-row">
            <button
              type="button"
              className={`cf-toggle-btn ${!spread ? "active" : ""}`}
              onClick={() => setSpread(false)}
            >
              sobreposição alta
            </button>
            <button
              type="button"
              className={`cf-toggle-btn ${spread ? "active" : ""}`}
              onClick={() => setSpread(true)}
            >
              sobreposição baixa
            </button>
          </div>
          <div className="cf-toy-row">
            {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => {
              const inA = A.includes(n);
              const inB = B.includes(n);
              const cls = inA && inB ? "in-both" : inA ? "in-a" : inB ? "in-b" : "in-neither";
              return (
                <span key={n} className={`cf-toy-ball ${cls}`}>
                  {n}
                </span>
              );
            })}
          </div>
          <p className="cf-toy-caption">{covered} de 12 números cobertos ao todo</p>
          <div className="cf-legend-row">
            <span className="cf-legend-item">
              <span className="cf-legend-dot" style={{ background: "var(--accent)" }} />
              só bilhete A
            </span>
            <span className="cf-legend-item">
              <span className="cf-legend-dot" style={{ background: "#209869" }} />
              só bilhete B
            </span>
            <span className="cf-legend-item">
              <span className="cf-legend-dot" style={{ background: "#d9931f" }} />
              os dois (desperdício)
            </span>
          </div>
          <p className="cf-small-note">
            Exemplo simplificado com 12 números pra visualizar. Na Lotofácil de verdade são
            25; a ideia é a mesma.
          </p>
        </div>
      </section>

      <section className="cf-band cf-band-alt">
        <div className="cf-inner">
          <p className="cf-label">02 · a ideia central</p>
          <h2 className="cf-title">Menos sobreposição, mais chance de UM deles acertar</h2>
          <p className="cf-body">
            Cada bilhete, sozinho, sempre teve a mesma chance de sempre. Prisma não mexe
            nisso. O que muda é a chance de pelo menos um bilhete da sua carteira bater o
            prêmio, quando as apostas se espalham em vez de se repetirem.
          </p>
          <div className="cf-venn-row">
            <div className="cf-venn-col">
              <div className="cf-venn-wrap">
                <span
                  className="cf-venn-circle"
                  style={{ background: "var(--accent)", left: 8 }}
                />
                <span className="cf-venn-circle" style={{ background: "#209869", left: 38 }} />
              </div>
              <span className="cf-venn-label">mais sobreposta</span>
            </div>
            <div className="cf-venn-col">
              <div className="cf-venn-wrap">
                <span
                  className="cf-venn-circle"
                  style={{ background: "var(--accent)", left: 8 }}
                />
                <span className="cf-venn-circle" style={{ background: "#209869", left: 76 }} />
              </div>
              <span className="cf-venn-label">menos sobreposta</span>
            </div>
          </div>
          <div className="cf-callout">
            Isso não muda as chances de cada bilhete. Muda a chance de pelo menos um, entre
            vários, acertar.
          </div>
        </div>
      </section>

      <section className="cf-band">
        <div className="cf-inner">
          <p className="cf-label">03 · o método</p>
          <h2 className="cf-title">Dois passos, repetidos rapidinho</h2>
          <div className="cf-steps-row">
            <div className="cf-step-card">
              <p className="cf-step-label">passo 1</p>
              <p className="cf-step-title">Preenchimento guloso</p>
              <p className="cf-step-body">
                A cada novo bilhete, o Prisma escolhe as dezenas que ainda apareceram menos na
                sua carteira.
              </p>
              <div className="cf-fill-row">
                {Array.from({ length: 8 }, (_, i) => (
                  <span
                    key={i}
                    className="cf-fill-dot"
                    style={{ animationDelay: `${i * 0.25}s` }}
                  />
                ))}
              </div>
            </div>
            <div className="cf-step-card">
              <p className="cf-step-label">passo 2</p>
              <p className="cf-step-title">Ajuste fino</p>
              <p className="cf-step-body">
                Depois, ele testa pequenas trocas ao acaso, tipo resolver um quebra-cabeça, e
                só guarda as que melhoram o resultado.
              </p>
              <div className="cf-swap-row">
                <span className="cf-swap-circle" />
                <span className="cf-swap-glyph">⇄</span>
                <span className="cf-swap-circle" />
              </div>
            </div>
          </div>
          <p className="cf-footnote">
            Tecnicamente: seleção gulosa de cobertura máxima, seguida de recozimento simulado
            (simulated annealing) minimizando a sobreposição total entre bilhetes.
          </p>
        </div>
      </section>

      <section className="cf-band cf-band-alt">
        <div className="cf-inner">
          <p className="cf-label">04 · os resultados</p>
          <h2 className="cf-title">Testado com simulação, não com achismo</h2>
          <p className="cf-body">
            Rodamos o otimizador de verdade na Lotofácil (15 dezenas por bilhete) e simulamos
            80 mil sorteios pra comparar a carteira espalhada com a baseline de bilhetes
            independentes, nas mesmas quantidades. Sem números ilustrativos — são os
            resultados reais do nosso próprio código.
          </p>
          <div className="cf-stat-callout">
            <span className="cf-stat-big">+6,3 pontos percentuais</span>
            <span className="cf-stat-sub">
              de chance a mais de acertar pelo menos um prêmio, apostando 5 bilhetes
              espalhados em vez de 5 independentes (49,1% vs 42,9%).
            </span>
          </div>
          <div className="cf-chart-legend-row">
            <span className="cf-chart-legend-item">
              <span className="cf-chart-swatch" style={{ background: "var(--accent)" }} />
              Prisma (espalhado)
            </span>
            <span className="cf-chart-legend-item">
              <span className="cf-chart-swatch" style={{ background: "var(--border)" }} />
              independente
            </span>
          </div>
          <div className="cf-chart-bars-row">
            {CHART.map((d) => (
              <div className="cf-chart-group" key={d.n}>
                <div className="cf-chart-bar-pair">
                  <span
                    className="cf-chart-bar"
                    style={{ height: Math.round(d.opt * 1.3), background: "var(--accent)" }}
                  />
                  <span
                    className="cf-chart-bar"
                    style={{ height: Math.round(d.rnd * 1.3), background: "var(--border)" }}
                  />
                </div>
                <span className="cf-chart-n-label">{d.n}</span>
              </div>
            ))}
          </div>
          <p className="cf-chart-caption">
            n = número de bilhetes na carteira. Valores medidos (Lotofácil, 15 dezenas, prêmio
            ≥11 acertos, 80 mil sorteios Monte Carlo).
          </p>
          <p className="cf-body">
            A vantagem é maior em quantidades pequenas (pico de +8,9pp em n=10) e praticamente
            some depois de umas 50 apostas, quando os dois métodos já cobrem quase tudo.
          </p>
          <details className="tech">
            <summary>Detalhes estatísticos</summary>
            <p>
              Baseado em otimização combinatória: seleção gulosa (garantia 1 − 1/e) seguida de
              recozimento simulado. A baseline "independente" é a fórmula fechada 1 −
              (1−p)ⁿ para bilhetes sem correlação; a curva "Prisma" vem de simulação de Monte
              Carlo sobre a carteira realmente gerada pelo otimizador, com a mesma seed
              reprodutível usada nos testes automatizados do projeto.
            </p>
          </details>
        </div>
      </section>

      <section className="cf-band">
        <div className="cf-inner">
          <p className="cf-label">05 · sem mágica</p>
          <h2 className="cf-title">O que muda. E o que não muda.</h2>
          <div className="cf-myth-fact-head">
            <span>mito</span>
            <span>fato</span>
          </div>
          {MYTH_FACTS.map((mf) => (
            <div className="cf-myth-fact-row" key={mf.myth}>
              <span className="cf-myth-col">
                <span className="cf-myth-glyph">✕</span>
                {mf.myth}
              </span>
              <span className="cf-fact-col">
                <span className="cf-fact-glyph">✓</span>
                {mf.fact}
              </span>
            </div>
          ))}
          <p className="cf-closing-line">
            Loteria continua tendo retorno médio negativo. Jogue com responsabilidade.
          </p>
        </div>
      </section>

      <div className="cf-footer-cta">
        <button type="button" className="btn-hero-primary" onClick={() => navigate("home")}>
          Já entendi, bora montar
        </button>
      </div>
    </div>
  );
}
