import { useState } from "react";
import { dd } from "../format";

interface Props {
  universe: number;
  pick: number;
  accent: string;
  bets: number[][];
  onAdd: (bet: number[]) => void;
  onRemove: (index: number) => void;
  /** Deslocamento de exibicao (ex.: Lotomania mostra 00-99 para 1..100 interno). */
  numberOffset?: number;
}

/**
 * Monta apostas completas do proprio usuario: seleciona `pick` dezenas e
 * adiciona à carteira. O otimizador completa os demais bilhetes.
 */
export default function MyBets({
  universe,
  pick,
  accent,
  bets,
  onAdd,
  onRemove,
  numberOffset = 0,
}: Props) {
  const label = (n: number) => dd(n - numberOffset);
  const [sel, setSel] = useState<Set<number>>(new Set());
  const nums = Array.from({ length: universe }, (_, i) => i + 1);

  function toggle(n: number) {
    const s = new Set(sel);
    if (s.has(n)) s.delete(n);
    else if (s.size < pick) s.add(n);
    setSel(s);
  }

  function add() {
    if (sel.size !== pick) return;
    onAdd([...sel].sort((a, b) => a - b));
    setSel(new Set());
  }

  const completo = sel.size === pick;

  return (
    <div className="mybets">
      <p className="grid-help">
        Marque <strong>{pick}</strong> dezenas para criar a sua aposta. O programa gera as
        outras para combinar melhor com a(s) sua(s).
      </p>

      <div className="grid" role="group" aria-label="Montar minha aposta">
        {nums.map((n) => {
          const on = sel.has(n);
          const disabled = !on && sel.size >= pick;
          return (
            <button
              key={n}
              type="button"
              className={`ball ${on ? "fixed" : ""}`}
              style={on ? { background: accent } : undefined}
              disabled={disabled}
              onClick={() => toggle(n)}
            >
              {label(n)}
            </button>
          );
        })}
      </div>

      <div className="mybets-actions">
        <span className={`mybets-count ${completo ? "ok" : ""}`}>
          {sel.size}/{pick} selecionadas
        </span>
        <button
          type="button"
          className="btn-secondary"
          disabled={!completo}
          onClick={add}
          style={completo ? { borderColor: accent, color: accent } : undefined}
        >
          + Adicionar minha aposta
        </button>
      </div>

      {bets.length > 0 && (
        <ul className="mybets-list">
          {bets.map((b, i) => (
            <li key={i}>
              <span className="mybets-chip" style={{ borderColor: accent }}>
                {b.map(label).join(" · ")}
              </span>
              <button
                type="button"
                className="mybets-remove"
                onClick={() => onRemove(i)}
                aria-label="Remover aposta"
                title="Remover"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
