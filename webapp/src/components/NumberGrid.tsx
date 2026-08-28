import { dd } from "../format";

interface Props {
  universe: number;
  fixed: Set<number>;
  excluded: Set<number>;
  onToggle: (n: number) => void;
  accent: string;
  /** Deslocamento de exibicao (ex.: Lotomania mostra 00-99 para 1..100 interno). */
  numberOffset?: number;
}

/**
 * Grade de dezenas. Clicar cicla: neutro -> fixa (obrigatoria) -> excluida -> neutro.
 */
export default function NumberGrid({
  universe,
  fixed,
  excluded,
  onToggle,
  accent,
  numberOffset = 0,
}: Props) {
  const nums = Array.from({ length: universe }, (_, i) => i + 1);
  return (
    <div className="grid" role="group" aria-label="Selecao de dezenas">
      {nums.map((n) => {
        const label = dd(n - numberOffset);
        const cls = fixed.has(n) ? "fixed" : excluded.has(n) ? "excluded" : "neutral";
        const style = cls === "fixed" ? { background: accent, borderColor: accent } : undefined;
        const title =
          cls === "fixed"
            ? `Dezena ${label}: fixa (entra em todos os bilhetes)`
            : cls === "excluded"
              ? `Dezena ${label}: excluida (nao aparece)`
              : `Dezena ${label}: clique para fixar`;
        return (
          <button
            key={n}
            type="button"
            className={`ball ${cls}`}
            style={style}
            title={title}
            onClick={() => onToggle(n)}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
