import pandas as pd, numpy as np, time, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

from lotofacil_optimizer import (
    N_UNIVERSE, N_DRAW,
    generate_ticket_pool, greedy_coverage_select,
    refine_overlap_sa, compute_overlap_matrix,
    prob_minimo_um_bilhete_independente,
)

N_SIM  = 50_000
SEED   = 3001
N_NEW  = [25, 30, 40, 50, 75, 100]

def make_draws_bool(rng):
    draws = rng.random((N_SIM, N_UNIVERSE)).argsort(axis=1)[:, :N_DRAW].astype(np.uint8) + 1
    d = np.zeros((N_SIM, N_UNIVERSE), dtype=np.uint8)
    d[np.repeat(np.arange(N_SIM), N_DRAW), draws.ravel() - 1] = 1
    return d

def eval_set(tickets, draws_bool):
    n = len(tickets)
    t = np.zeros((n, N_UNIVERSE), dtype=np.uint8)
    t[np.repeat(np.arange(n), N_DRAW), tickets.ravel() - 1] = 1
    hits = draws_bool @ t.T
    return float(np.any(hits >= 11, axis=1).mean())

def mean_overlap(tickets):
    if len(tickets) < 2:
        return 0.0
    m = compute_overlap_matrix(tickets)
    return float(m[np.triu_indices(len(tickets), k=1)].mean())

# --- Run extended benchmark ---
rng = np.random.default_rng(SEED)
records = []
total = len(N_NEW) * 30
step = 0
t0 = time.time()

print("Rodando extensao do benchmark: n =", N_NEW)
print()

for n in N_NEW:
    p_ref   = prob_minimo_um_bilhete_independente(n)
    n_pool  = max(500, n * 20)
    sa_iter = min(500 + 100 * n, 2000)
    draws_bool = make_draws_bool(rng)
    print(f"  n={n:3d}  ref={p_ref:.5f}  pool={n_pool}  SA_iter={sa_iter}")

    for trial in range(30):
        rand_t = generate_ticket_pool(n, rng)
        p_r    = eval_set(rand_t, draws_bool)
        ov_r   = mean_overlap(rand_t)

        pool  = generate_ticket_pool(n_pool, rng)
        gr_t  = greedy_coverage_select(pool, n)
        p_g   = eval_set(gr_t, draws_bool)
        ov_g  = mean_overlap(gr_t)

        sa_t  = refine_overlap_sa(gr_t.copy(), rng, n_iter=sa_iter)
        p_s   = eval_set(sa_t, draws_bool)
        ov_s  = mean_overlap(sa_t)

        records.append(dict(
            n=n, trial=trial,
            p_random=p_r,  overlap_random=ov_r,
            p_greedy=p_g,  overlap_greedy=ov_g,
            p_sa=p_s,      overlap_sa=ov_s,
            p_ref=p_ref,
        ))

        step += 1
        eta = (time.time() - t0) / step * (total - step) / 60
        print(f"    [{step:3d}/{total}] rand={p_r:.4f}  greedy={p_g:.4f}  sa={p_s:.4f}  ETA {eta:.1f}min   ",
              end="\r", flush=True)

    print(" " * 80, end="\r")

print(f"\nTempo extensao: {time.time()-t0:.0f}s")

# --- Combina com dados anteriores ---
df_old = pd.read_csv("benchmark_results.csv")
df_new = pd.DataFrame(records)
df_all = pd.concat([df_old, df_new], ignore_index=True)
df_all.to_csv("benchmark_results_full.csv", index=False)

# --- Sumariza ---
z = 1.96
rows = []
for n, g in df_all.groupby("n"):
    ref = g["p_ref"].iloc[0]
    p_rand_mean = g["p_random"].mean()
    for strat, p_col, ov_col in [
        ("aleatorio", "p_random",  "overlap_random"),
        ("greedy",    "p_greedy",  "overlap_greedy"),
        ("annealing", "p_sa",      "overlap_sa"),
    ]:
        mu = g[p_col].mean()
        se = g[p_col].std(ddof=1) / len(g) ** 0.5
        rows.append(dict(
            n=n, estrategia=strat,
            p_media=round(mu, 5), p_ci95=round(z * se, 5),
            overlap_medio=round(g[ov_col].mean(), 3),
            p_ref=round(ref, 5),
            ganho_vs_random=round((mu / p_rand_mean - 1) * 100, 2) if strat != "aleatorio" else 0.0,
        ))
summary = pd.DataFrame(rows)
summary.to_csv("benchmark_summary_full.csv", index=False)

# --- Tabela ---
print()
print("=" * 92)
print("  RESULTADOS COMPLETOS: P(>=11) em ao menos um bilhete")
print("=" * 92)
print(f"  {'n':>4}  {'Aleatorio':>14}  {'Greedy':>14}  {'SA':>14}  {'Ref.teorica':>11}  {'SA-Rand':>8}")
print("  " + "-" * 82)
for n, g in summary.groupby("n"):
    s = g.set_index("estrategia")
    def f(st):
        return f"{s.loc[st,'p_media']:.4f}+-{s.loc[st,'p_ci95']:.4f}"
    gain = s.loc["annealing", "ganho_vs_random"]
    ref  = s.loc["aleatorio", "p_ref"]
    print(f"  {n:4d}  {f('aleatorio'):>14}  {f('greedy'):>14}  {f('annealing'):>14}  {ref:11.5f}  {gain:>+7.2f}%")
print("=" * 92)

# --- t-test novos n ---
print()
print("  Paired t-test (SA vs Aleatorio) -- novos n:")
print(f"  {'n':>4}  {'ganho':>8}  {'t':>7}  {'p':>10}  {'Cohen_d':>8}  sig")
print("  " + "-" * 50)
for n in N_NEW:
    g    = df_all[df_all.n == n]
    diff = g["p_sa"].values - g["p_random"].values
    t, p = stats.ttest_rel(g["p_sa"].values, g["p_random"].values)
    d    = diff.mean() / diff.std(ddof=1)
    sig  = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "n.s."))
    print(f"  {n:4d}  {diff.mean():+8.4f}  {t:7.2f}  {p:10.2e}  {d:8.3f}  {sig}")

# --- Grafico completo ---
ns_all  = sorted(summary["n"].unique())
ref_map = {n: summary[(summary.n==n) & (summary.estrategia=="aleatorio")]["p_ref"].values[0]
           for n in ns_all}

strat_cfg = [
    ("aleatorio", "gray",       "Aleatorio",  "o"),
    ("greedy",    "steelblue",  "Greedy",     "s"),
    ("annealing", "darkorange", "Greedy+SA",  "^"),
]

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Painel 1: P(>=11)
axes[0].plot(ns_all, [ref_map[n] for n in ns_all], "k--", lw=1.5, alpha=0.6, label="Limite teorico (independencia)")
for st, col, lab, mk in strat_cfg:
    sub = summary[summary.estrategia == st].set_index("n")
    y   = [sub.loc[n, "p_media"] for n in ns_all]
    ye  = [sub.loc[n, "p_ci95"]  for n in ns_all]
    axes[0].errorbar(ns_all, y, yerr=ye, marker=mk, color=col, lw=2, capsize=3, label=lab)
axes[0].axvline(20.5, color="red", ls=":", alpha=0.4, lw=1, label="n<=20 / n>20")
axes[0].set_title("P(>=11 acertos em ao menos um bilhete)")
axes[0].set_xlabel("n bilhetes")
axes[0].set_ylabel("Probabilidade")
axes[0].legend(fontsize=8)
axes[0].grid(alpha=0.3)

# Painel 2: ganho absoluto SA vs Aleatorio (barras)
gains = []
for n in ns_all:
    s = summary[summary.n == n].set_index("estrategia")
    gains.append(s.loc["annealing", "p_media"] - s.loc["aleatorio", "p_media"])
colors_bar = ["#e8e8e8" if n <= 20 else "darkorange" for n in ns_all]
axes[1].bar(range(len(ns_all)), [g * 100 for g in gains], color=colors_bar, edgecolor="black", alpha=0.85)
axes[1].set_xticks(range(len(ns_all)))
axes[1].set_xticklabels([str(n) for n in ns_all], fontsize=8)
axes[1].set_title("Ganho absoluto: SA vs Aleatorio")
axes[1].set_xlabel("n bilhetes")
axes[1].set_ylabel("Ganho (pontos percentuais)")
axes[1].grid(alpha=0.3, axis="y")
for i, (n, g) in enumerate(zip(ns_all, gains)):
    if g > 0.001:
        axes[1].text(i, g * 100 + 0.1, f"{g*100:.1f}", ha="center", va="bottom", fontsize=7)

# Painel 3: sobreposicao media
min_ov = max(0, 2 * N_DRAW - N_UNIVERSE)
axes[2].axhline(min_ov, color="black", ls="--", lw=1.5, alpha=0.6, label=f"Minimo teorico por par ({min_ov})")
for st, col, lab, mk in strat_cfg:
    sub = summary[summary.estrategia == st].set_index("n")
    y   = [sub.loc[n, "overlap_medio"] for n in ns_all]
    axes[2].plot(ns_all, y, marker=mk, color=col, lw=2, label=lab)
axes[2].set_title("Sobreposicao media entre pares de bilhetes")
axes[2].set_xlabel("n bilhetes")
axes[2].set_ylabel("Dezenas em comum (media)")
axes[2].legend(fontsize=8)
axes[2].grid(alpha=0.3)

plt.suptitle(
    "Benchmark completo n=1 a 100  |  30-50 trials x 50k sorteios MC  |  design pareado",
    fontsize=10,
)
plt.tight_layout()
plt.savefig("benchmark_plot_full.png", dpi=150, bbox_inches="tight")
print("\nGrafico salvo: benchmark_plot_full.png")

try:
    import winsound
    for freq, dur in [(440,150),(550,150),(660,150),(880,500)]:
        winsound.Beep(freq, dur)
except Exception:
    pass
