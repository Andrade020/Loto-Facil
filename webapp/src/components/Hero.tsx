import { LOTTERIES } from "../lotteries";
import type { Route } from "../useHashRoute";

const TRUST = [
  "Otimização combinatória, não achismo",
  "Não prevê resultado, só melhora a cobertura",
  "Independente, sem vínculo com a Caixa",
];

const STEPS = [
  { n: "01", title: "Escolha", body: "a loteria e quantos bilhetes cabem no orçamento" },
  { n: "02", title: "Espalhe", body: "Prisma distribui as dezenas pra minimizar repetição" },
  { n: "03", title: "Entenda", body: "veja suas chances reais, em números claros" },
];

export default function Hero({ navigate }: { navigate: (r: Route) => void }) {
  const scrollToTool = () => {
    document.getElementById("tool")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <>
      <header className="hero">
        <p className="hero-tag">para as 6 loterias da Caixa</p>
        <h1>Método, não palpite.</h1>
        <p className="subtitle">
          Prisma organiza suas apostas na Lotofácil, na Mega-Sena e nas outras loterias da
          Caixa com um otimizador combinatório: <strong>mais cobertura, menos sobreposição</strong>{" "}
          entre bilhetes, sem prometer prever números.
        </p>
        <div className="hero-cta-row">
          <button type="button" className="btn-hero-primary" onClick={scrollToTool}>
            Montar minha carteira
          </button>
          <button
            type="button"
            className="btn-hero-secondary"
            onClick={() => navigate("como-funciona")}
          >
            Entender o método
          </button>
        </div>
      </header>

      <div className="trust-row">
        {TRUST.map((t) => (
          <div className="trust-item" key={t}>
            {t}
          </div>
        ))}
      </div>

      <div className="how-mini">
        {STEPS.map((s) => (
          <div className="how-mini-step" key={s.n}>
            <span className="how-mini-n">{s.n}</span>
            <strong className="how-mini-title">{s.title}</strong>
            <span className="how-mini-body">{s.body}</span>
          </div>
        ))}
      </div>

      <p className="lottery-strip">{LOTTERIES.map((l) => l.nome).join(" · ")}</p>
    </>
  );
}
