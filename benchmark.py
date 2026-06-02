#!/usr/bin/env python3
"""
benchmark.py

Compara três estratégias de seleção de bilhetes para a Lotofácil:

  aleatorio  — n bilhetes completamente aleatórios (sem estratégia)
  greedy     — n bilhetes por cobertura máxima (Greedy Set Cover)
  annealing  — greedy refinado por SA (minimiza sobreposição pareada)

Design pareado:
  Para cada valor de n, os MESMOS N_SIM sorteios aleatórios são usados
  para avaliar todas as estratégias em todos os trials. Isso elimina a
  variância do Monte Carlo da comparação — o que resta é apenas a
  variância causada pela escolha dos bilhetes.

Saídas:
  benchmark_results.csv  — dados brutos (uma linha por trial)
  benchmark_summary.csv  — média +- IC 95% por (n, estratégia)
  benchmark_plot.png     — gráfico de resultados
  Som ao terminar        — winsound.Beep (Windows)
"""

import sys
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from lotofacil_optimizer import (
    N_UNIVERSE,
    N_DRAW,
    generate_ticket_pool,
    greedy_coverage_select,
    refine_overlap_sa,
    compute_overlap_matrix,
    prob_minimo_um_bilhete_independente,
)

# ─── Parâmetros ────────────────────────────────────────────────────────────
N_LIST   = [1, 2, 3, 5, 7, 10, 15, 20]   # valores de n a testar
N_SIM    = 50_000                          # sorteios MC compartilhados por n
SEED     = 2024

# Trials reduzidos para n grande: SA é mais lento lá, mas o sinal ainda é claro
def n_trials(n: int) -> int:
    if n <= 5:  return 50
    if n <= 10: return 40
    return 30   # n = 15, 20

# SA_ITER cresce com n mas com cap: o objetivo é comparação, não otimização máxima
SA_BASE_ITER  = 500
SA_SCALE      = 100    # SA_ITER = min(SA_BASE_ITER + SA_SCALE * n, SA_MAX_ITER)
SA_MAX_ITER   = 2_000  # cap para n grandes não explodirem em tempo

N_POOL_FACTOR = 20     # pool = max(300, n * N_POOL_FACTOR)

OUT_CSV_RAW = "benchmark_results.csv"
OUT_CSV_SUM = "benchmark_summary.csv"
OUT_PLOT    = "benchmark_plot.png"
# ───────────────────────────────────────────────────────────────────────────


def make_draws_bool(n_sim: int, rng: np.random.Generator) -> np.ndarray:
    """
    Gera n_sim sorteios uniformes e retorna matriz booleana (n_sim, 25).
    Usa argsort de floats aleatórios — equivalente a choice(replace=False)
    mas completamente vetorizado.
    """
    draws = (
        rng.random((n_sim, N_UNIVERSE)).argsort(axis=1)[:, :N_DRAW].astype(np.uint8) + 1
    )
    d_bool = np.zeros((n_sim, N_UNIVERSE), dtype=np.uint8)
    d_bool[np.repeat(np.arange(n_sim), N_DRAW), draws.ravel() - 1] = 1
    return d_bool


def eval_set(tickets: np.ndarray, draws_bool: np.ndarray) -> float:
    """
    Estima P(>=11 em ao menos um bilhete) contra sorteios pré-gerados.
    Complexidade: O(N_SIM x 25 x n) via multiplicação matricial uint8.
    """
    n = len(tickets)
    t_bool = np.zeros((n, N_UNIVERSE), dtype=np.uint8)
    t_bool[np.repeat(np.arange(n), N_DRAW), tickets.ravel() - 1] = 1
    hits = draws_bool @ t_bool.T    # (N_SIM, n)
    return float(np.any(hits >= 11, axis=1).mean())


def mean_overlap(tickets: np.ndarray) -> float:
    """Média das sobreposições pareadas. 0 para n < 2."""
    if len(tickets) < 2:
        return 0.0
    m = compute_overlap_matrix(tickets)
    return float(m[np.triu_indices(len(tickets), k=1)].mean())


# ─── Loop principal ────────────────────────────────────────────────────────

def run_benchmark(rng: np.random.Generator) -> pd.DataFrame:
    records = []
    total_trials = sum(n_trials(n) for n in N_LIST)
    step = 0
    t0 = time.time()

    print(f"{'='*68}")
    print(f"  BENCHMARK — {len(N_LIST)} valores de n x até {max(n_trials(n) for n in N_LIST)} trials x 3 estratégias")
    print(f"  N_SIM = {N_SIM:,} sorteios compartilhados por n  (design pareado)")
    print(f"{'='*68}")

    for n in N_LIST:
        p_ref     = prob_minimo_um_bilhete_independente(n)
        sa_iter   = min(SA_BASE_ITER + SA_SCALE * n, SA_MAX_ITER)
        n_pool    = max(300, n * N_POOL_FACTOR)
        n_trials_ = n_trials(n)

        # Sorteios compartilhados para este n — todos os trials usam os mesmos
        draws_bool = make_draws_bool(N_SIM, rng)

        print(f"\n  n={n:2d}  ref={p_ref:.4f}  SA_iter={sa_iter}  trials={n_trials_}  pool={n_pool}")

        for trial in range(n_trials_):

            # ── Aleatório ────────────────────────────────────────────────
            rand_t = generate_ticket_pool(n, rng)
            p_r    = eval_set(rand_t, draws_bool)
            ov_r   = mean_overlap(rand_t)

            # ── Greedy ───────────────────────────────────────────────────
            pool   = generate_ticket_pool(n_pool, rng)
            gr_t   = greedy_coverage_select(pool, n)
            p_g    = eval_set(gr_t, draws_bool)
            ov_g   = mean_overlap(gr_t)

            # ── Greedy + SA ───────────────────────────────────────────────
            sa_t   = refine_overlap_sa(gr_t.copy(), rng, n_iter=sa_iter)
            p_s    = eval_set(sa_t, draws_bool)
            ov_s   = mean_overlap(sa_t)

            records.append(dict(
                n=n,           trial=trial,
                p_random=p_r,  overlap_random=ov_r,
                p_greedy=p_g,  overlap_greedy=ov_g,
                p_sa=p_s,      overlap_sa=ov_s,
                p_ref=p_ref,
            ))

            step    += 1
            elapsed  = time.time() - t0
            eta_min  = (elapsed / step) * (total_trials - step) / 60
            print(
                f"    [{step:3d}/{total_trials}] trial={trial+1:2d}  "
                f"rand={p_r:.4f}  greedy={p_g:.4f}  sa={p_s:.4f}  "
                f"ETA {eta_min:.1f}min   ",
                end="\r",
                flush=True,
            )

        # limpa linha de progresso antes de imprimir o próximo n
        print(" " * 80, end="\r")

    elapsed_total = time.time() - t0
    print(f"\n  Tempo total: {elapsed_total/60:.1f} min  ({elapsed_total:.0f}s)")
    return pd.DataFrame(records)


# ─── Estatísticas ──────────────────────────────────────────────────────────

def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega por (n, estratégia): média, IC 95%, overlap médio."""
    rows = []
    z = 1.96   # IC 95%

    for n, g in df.groupby("n"):
        ref = g["p_ref"].iloc[0]
        p_rand_mean = g["p_random"].mean()

        for strat, p_col, ov_col in [
            ("aleatorio", "p_random",  "overlap_random"),
            ("greedy",    "p_greedy",  "overlap_greedy"),
            ("annealing", "p_sa",      "overlap_sa"),
        ]:
            mu  = g[p_col].mean()
            se  = g[p_col].std(ddof=1) / len(g) ** 0.5
            rows.append(dict(
                n                = n,
                estrategia       = strat,
                p_media          = round(mu, 5),
                p_ci95           = round(z * se, 5),
                overlap_medio    = round(g[ov_col].mean(), 3),
                p_ref            = round(ref, 5),
                ganho_vs_random  = round((mu / p_rand_mean - 1) * 100, 2)
                                   if p_rand_mean > 0 else 0.0,
            ))

    return pd.DataFrame(rows)


# ─── Tabela no terminal ────────────────────────────────────────────────────

def print_table(summary: pd.DataFrame) -> None:
    sep = "=" * 90
    print(f"\n{sep}")
    print("  RESULTADOS: P(>=11 em ao menos um bilhete)  [média +- IC95%]")
    print(sep)
    print(
        f"  {'n':>3}  {'Aleatório':>14}  {'Greedy':>14}  "
        f"{'Greedy+SA':>14}  {'Ref. teórica':>13}  {'SA vs Rand':>10}"
    )
    print(f"  {'-'*86}")

    for n, g in summary.groupby("n"):
        s = g.set_index("estrategia")

        def fmt(strat: str) -> str:
            return f"{s.loc[strat,'p_media']:.4f}+-{s.loc[strat,'p_ci95']:.4f}"

        gain = s.loc["annealing", "ganho_vs_random"]
        print(
            f"  {n:3d}  {fmt('aleatorio'):>14}  {fmt('greedy'):>14}  "
            f"{fmt('annealing'):>14}  {s.loc['aleatorio','p_ref']:.5f}       "
            f"{gain:>+8.1f}%"
        )

    print(sep)
    print(
        "  Ref. teórica = P(>=11 em ao menos 1 bilhete) assumindo independência total\n"
        "  (impossível na prática por sobreposição mínima forçada de 5 dezenas por par)"
    )
    print(sep)


# ─── Gráficos ──────────────────────────────────────────────────────────────

def plot_results(summary: pd.DataFrame, out_path: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ns = sorted(summary["n"].unique())
    ref = {
        n: summary[(summary.n == n) & (summary.estrategia == "aleatorio")]["p_ref"].values[0]
        for n in ns
    }

    strat_cfg = [
        ("aleatorio", "gray",       "Aleatório",         "o", "-"),
        ("greedy",    "steelblue",  "Greedy cobertura",  "s", "-"),
        ("annealing", "darkorange", "Greedy + SA",       "^", "-"),
    ]

    # ── Painel 1: P(>=11 em ao menos um) ──────────────────────────────────
    axes[0].plot(
        ns, [ref[n] for n in ns], "k--", lw=1.5, alpha=0.6,
        label="Limite teórico (independência perfeita)",
    )
    for strat, color, label, marker, ls in strat_cfg:
        sub = summary[summary.estrategia == strat].set_index("n")
        y   = [sub.loc[n, "p_media"] for n in ns]
        ye  = [sub.loc[n, "p_ci95"]  for n in ns]
        axes[0].errorbar(
            ns, y, yerr=ye,
            marker=marker, color=color, lw=2, capsize=4,
            label=label, linestyle=ls,
        )
    axes[0].set_title("P(>=11 acertos em ao menos um bilhete)", fontsize=11)
    axes[0].set_xlabel("Número de bilhetes (n)")
    axes[0].set_ylabel("Probabilidade estimada")
    axes[0].legend(fontsize=9)
    axes[0].grid(alpha=0.3)
    axes[0].set_xticks(ns)

    # ── Painel 2: sobreposição média ──────────────────────────────────────
    min_ov = max(0, 2 * N_DRAW - N_UNIVERSE)
    axes[1].axhline(
        min_ov, color="black", lw=1.5, ls="--", alpha=0.6,
        label=f"Mínimo teórico por par (= {min_ov} dezenas)",
    )
    for strat, color, label, marker, ls in strat_cfg:
        sub = summary[summary.estrategia == strat].set_index("n")
        y   = [sub.loc[n, "overlap_medio"] for n in ns]
        axes[1].plot(
            ns, y, marker=marker, color=color, lw=2,
            label=label, linestyle=ls,
        )
    axes[1].set_title("Sobreposição média entre pares de bilhetes", fontsize=11)
    axes[1].set_xlabel("Número de bilhetes (n)")
    axes[1].set_ylabel("Dezenas em comum (média por par)")
    axes[1].legend(fontsize=9)
    axes[1].grid(alpha=0.3)
    axes[1].set_xticks(ns)

    plt.suptitle(
        f"Benchmark: Aleatório x Greedy x Greedy+SA  —  "
        f"30-50 trials x {N_SIM:,} sorteios MC compartilhados (design pareado)",
        fontsize=10,
    )
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\n  Gráfico salvo em: {out_path}")
    plt.show()


# ─── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    rng = np.random.default_rng(SEED)

    df = run_benchmark(rng)
    df.to_csv(OUT_CSV_RAW, index=False)
    print(f"\n  Dados brutos: {OUT_CSV_RAW}")

    summary = summarize(df)
    summary.to_csv(OUT_CSV_SUM, index=False)
    print(f"  Resumo:       {OUT_CSV_SUM}")

    print_table(summary)
    plot_results(summary, OUT_PLOT)

    # ── Notificação sonora ao terminar (Windows) ──────────────────────────
    try:
        import winsound
        for freq, dur in [(440, 150), (550, 150), (660, 150), (880, 500)]:
            winsound.Beep(freq, dur)
    except Exception:
        pass

    print(f"\n{'='*68}")
    print("  Benchmark concluido. Resultados em:")
    print(f"    {OUT_CSV_RAW}")
    print(f"    {OUT_CSV_SUM}")
    print(f"    {OUT_PLOT}")
    print(f"{'='*68}")
