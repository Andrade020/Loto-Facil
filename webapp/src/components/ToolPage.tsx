import { useEffect, useMemo, useState } from "react";
import { LOTTERIES, PRICES_DATE, applyRemotePrices, getLottery, precoBilhete } from "../lotteries";
import { brl } from "../format";
import { phaseLabel, useOptimizer } from "../useOptimizer";
import NumberGrid from "./NumberGrid";
import MyBets from "./MyBets";
import ResultView from "./ResultView";

export default function ToolPage() {
  const [lotteryId, setLotteryId] = useState(LOTTERIES[0].id);
  const lot = getLottery(lotteryId);

  // Tenta atualizar precos via prices.json (opcional); senao usa os embutidos.
  const [pricesDate, setPricesDate] = useState(PRICES_DATE);
  useEffect(() => {
    applyRemotePrices().then((changed) => {
      if (changed) setPricesDate(PRICES_DATE);
    });
  }, []);

  const [nBilhetes, setNBilhetes] = useState(5);
  const [pick, setPick] = useState(lot.minPick);
  const [fixed, setFixed] = useState<Set<number>>(new Set());
  const [excluded, setExcluded] = useState<Set<number>>(new Set());
  const [myBets, setMyBets] = useState<number[][]>([]);
  const [refine, setRefine] = useState(true);
  const [showGrid, setShowGrid] = useState(false);
  const [showMyBets, setShowMyBets] = useState(false);

  const { running, progress, result, error, run, reset } = useOptimizer();

  function selectLottery(id: string) {
    if (id === lotteryId) return;
    const l = getLottery(id);
    setLotteryId(id);
    setPick(l.minPick);
    setFixed(new Set());
    setExcluded(new Set());
    setMyBets([]); // dezenas sao de outro universo
    reset(); // limpa o resultado do jogo anterior
  }

  function changePick(v: number) {
    setPick(v);
    if (fixed.size > v) setFixed(new Set());
    if (myBets.length > 0) setMyBets([]); // apostas tinham outro tamanho
    if (result) reset();
  }

  function toggleNum(n: number) {
    // neutro -> fixa -> excluida -> neutro
    const f = new Set(fixed);
    const e = new Set(excluded);
    if (f.has(n)) {
      f.delete(n);
      e.add(n);
    } else if (e.has(n)) {
      e.delete(n);
    } else {
      f.add(n);
    }
    setFixed(f);
    setExcluded(e);
  }

  const totalBilhetes = Math.max(nBilhetes, myBets.length);
  const precoUnit = precoBilhete(lot, pick);
  const custoTotal = precoUnit * totalBilhetes;
  const allowedCount = lot.universe - excluded.size;

  const validacao = useMemo(() => {
    if (fixed.size > pick)
      return `Você fixou ${fixed.size} dezenas, mais que as ${pick} por bilhete.`;
    if (allowedCount < pick)
      return `Restam ${allowedCount} dezenas permitidas, menos que as ${pick} por bilhete.`;
    return null;
  }, [fixed.size, pick, allowedCount]);

  function gerar() {
    if (validacao) return;
    run({
      lotteryId,
      nBilhetes: totalBilhetes,
      pick,
      fixed: [...fixed],
      excluded: [...excluded],
      seedTickets: myBets,
      numSim: 60000,
      refine,
    });
  }

  return (
    <div id="tool" className="tool" style={{ ["--accent" as string]: lot.cor }}>
      <div className="lottery-tabs">
        {LOTTERIES.map((l) => (
          <button
            key={l.id}
            type="button"
            className={`lottery-tab ${l.id === lotteryId ? "active" : ""}`}
            style={l.id === lotteryId ? { background: l.cor, borderColor: l.cor } : { borderColor: l.cor, color: l.cor }}
            onClick={() => selectLottery(l.id)}
          >
            {l.nome}
            <small>
              {l.minPick === l.maxPick ? `${l.minPick}` : `${l.minPick}–${l.maxPick}`} de{" "}
              {l.universe} · prêmio ≥ {l.premioMin}
            </small>
          </button>
        ))}
      </div>

      {lot.notaPremiacao && (
        <div className="aviso-box aviso-box-inline">ℹ {lot.notaPremiacao}</div>
      )}

      <section className="controls card">
        <div className="control-row">
          <Stepper
            label="Quantos bilhetes?"
            value={nBilhetes}
            min={1}
            max={100}
            onChange={setNBilhetes}
          />
          <Stepper
            label="Dezenas por bilhete"
            value={pick}
            min={lot.minPick}
            max={lot.maxPick}
            onChange={changePick}
            hint={pick > lot.minPick ? `${brl(precoUnit)} cada` : undefined}
          />
        </div>

        <label className="toggle">
          <input
            type="checkbox"
            checked={refine}
            onChange={(e) => setRefine(e.target.checked)}
          />
          Caprichar na combinação (recomendado)
        </label>

        <button
          type="button"
          className={`feature-toggle ${showMyBets ? "open" : ""}`}
          style={{ borderColor: lot.cor, color: lot.cor }}
          onClick={() => setShowMyBets((s) => !s)}
        >
          <span className="feature-toggle-icon" style={{ background: lot.cor }}>
            +
          </span>
          <span className="feature-toggle-text">
            Quero incluir minhas próprias apostas
            <small>monte seus jogos e deixe o resto por nossa conta</small>
          </span>
          {myBets.length > 0 && (
            <span className="feature-toggle-badge" style={{ background: lot.cor }}>
              {myBets.length}
            </span>
          )}
        </button>
        {showMyBets && (
          <div className="grid-wrap">
            <MyBets
              universe={lot.universe}
              pick={pick}
              accent={lot.cor}
              numberOffset={lot.numberOffset}
              bets={myBets}
              onAdd={(b) =>
                setMyBets((prev) => {
                  const next = [...prev, b];
                  if (next.length > nBilhetes) setNBilhetes(next.length);
                  return next;
                })
              }
              onRemove={(i) => setMyBets((prev) => prev.filter((_, j) => j !== i))}
            />
          </div>
        )}

        <button
          type="button"
          className="grid-toggle"
          onClick={() => setShowGrid((s) => !s)}
        >
          {showGrid ? "▾" : "▸"} Dezenas fixas / excluídas
          {(fixed.size > 0 || excluded.size > 0) &&
            ` (${fixed.size} fixas, ${excluded.size} excluídas)`}
        </button>
        {showGrid && (
          <div className="grid-wrap">
            <p className="grid-help">
              Clique numa dezena para <span className="lg-fixed">fixá-la</span> (entra em
              todos os bilhetes), de novo para <span className="lg-excluded">excluí-la</span>,
              e de novo para liberar.
            </p>
            <NumberGrid
              universe={lot.universe}
              fixed={fixed}
              excluded={excluded}
              onToggle={toggleNum}
              accent={lot.cor}
              numberOffset={lot.numberOffset}
            />
            {(fixed.size > 0 || excluded.size > 0) && (
              <button
                type="button"
                className="link-btn"
                onClick={() => {
                  setFixed(new Set());
                  setExcluded(new Set());
                }}
              >
                limpar seleção
              </button>
            )}
          </div>
        )}

        <div className="cta-row">
          <div className="cost-preview">
            Custo estimado: <strong>{brl(custoTotal)}</strong>
            <small>
              {totalBilhetes} × {brl(precoUnit)}
              {myBets.length > 0 &&
                ` (${myBets.length} suas + ${totalBilhetes - myBets.length} geradas)`}{" "}
              · preços {pricesDate}
            </small>
          </div>
          <button
            type="button"
            className="btn-primary"
            style={{ background: lot.cor }}
            disabled={running || !!validacao}
            onClick={gerar}
          >
            {running ? "Otimizando…" : "Gerar bilhetes"}
          </button>
        </div>

        {validacao && <p className="erro">{validacao}</p>}
      </section>

      {running && progress && (
        <section className="card progress-card">
          <div className="progress-label">{phaseLabel(progress.phase)}…</div>
          <div className="progress-track">
            <div
              className="progress-bar"
              style={{ width: `${Math.round(progress.frac * 100)}%`, background: lot.cor }}
            />
          </div>
        </section>
      )}

      {error && <section className="card erro-box">⚠ {error}</section>}

      {result && !running && result.lotteryId === lotteryId && (
        <>
          {result.warnings.map((w, i) => (
            <div key={i} className="aviso-box">
              ⚠ {w}
            </div>
          ))}
          <ResultView result={result} fixed={fixed} />
        </>
      )}
    </div>
  );
}

function Stepper({
  label,
  value,
  min,
  max,
  onChange,
  hint,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (v: number) => void;
  hint?: string;
}) {
  const clamp = (v: number) => Math.max(min, Math.min(max, v));
  return (
    <div className="stepper">
      <label>{label}</label>
      <div className="stepper-row">
        <button type="button" onClick={() => onChange(clamp(value - 1))} disabled={value <= min}>
          −
        </button>
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          onChange={(e) => onChange(clamp(parseInt(e.target.value || String(min), 10)))}
        />
        <button type="button" onClick={() => onChange(clamp(value + 1))} disabled={value >= max}>
          +
        </button>
      </div>
      <small className="stepper-hint">{hint ?? `${min}–${max}`}</small>
    </div>
  );
}
