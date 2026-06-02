"""
lotofacil_optimizer.py

Gerador de apostas baseado em otimização combinatória de cobertura.

Objetivo matemático rigoroso:
  Dado um orçamento de n bilhetes, escolher os n subconjuntos de 15 dezenas
  de {1..25} que MAXIMIZAM P(≥11 acertos em pelo menos um bilhete).

Fundamento:
  P(≥11 em pelo menos um) = 1 − P(nenhum ≥11)
  P(nenhum ≥11) é minimizado quando os bilhetes são o mais "independentes"
  possível — ou seja, quando a sobreposição pareada entre eles é mínima.
  Minimizar sobreposição total é portanto o objetivo matemático correto.

Nota sobre valor esperado:
  O VE de cada bilhete é NEGATIVO (a loteria é um imposto sobre probabilidade).
  O algoritmo não muda esse fato — ele apenas distribui o risco de forma ótima
  para um dado número de apostas, maximizando P(algum prêmio).

Nota sobre "padrões humanos" (H score):
  Evitar combinações populares reduz divisão de prêmio SE soubermos quais
  combinações outros apostadores escolhem. Sem a distribuição real de apostas
  da Lotofácil, qualquer H score é especulação. Por isso, score_human_batch()
  existe como ferramenta de ANÁLISE SEPARADA, não como parte da otimização.
"""

from __future__ import annotations

from math import comb
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
N_UNIVERSE = 25   # dezenas disponíveis: 1 a 25
N_DRAW = 15       # dezenas por bilhete

# ---------------------------------------------------------------------------
# Referência teórica: probabilidade por bilhete (distribuição hipergeométrica)
# ---------------------------------------------------------------------------

def prob_por_acertos() -> dict[int, float]:
    """
    P(k acertos em um bilhete) pela distribuição hipergeométrica exata.
    Válida para qualquer combinação de 15 dezenas — todas são equiprováveis.

    P(k) = C(15,k) × C(10, 15−k) / C(25,15)
    """
    total = comb(25, 15)
    return {k: comb(15, k) * comb(10, 15 - k) / total for k in range(11, 16)}


def prob_minimo_um_bilhete_independente(n: int) -> float:
    """
    Limite superior teórico de P(≥11 em ao menos um bilhete) assumindo
    independência total entre os bilhetes (sobreposição zero — impossível
    na prática, mas serve de referência).

    P = 1 − (1 − p_single)^n
    """
    p_single = sum(prob_por_acertos().values())
    return 1.0 - (1.0 - p_single) ** n


# ---------------------------------------------------------------------------
# Módulo 1 — Geração de bilhetes candidatos
# ---------------------------------------------------------------------------

def generate_ticket_pool(n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Gera n bilhetes aleatórios uniformes sem restrições arbitrárias.

    Todas as combinações de 15 dezenas de {1..25} são igualmente prováveis
    de ser sorteadas, portanto nenhum filtro de soma/paridade é matematicamente
    justificado aqui.

    Returns
    -------
    ndarray shape (n, 15), linhas ordenadas, dtype int32
    """
    pool = rng.random((n, N_UNIVERSE)).argsort(axis=1)[:, :N_DRAW] + 1
    pool.sort(axis=1)
    return pool.astype(np.int32)


# ---------------------------------------------------------------------------
# Módulo 2 — Seleção gulosa por cobertura máxima
# ---------------------------------------------------------------------------

def greedy_coverage_select(pool: np.ndarray, n: int) -> np.ndarray:
    """
    Seleciona n bilhetes do pool pelo algoritmo Greedy Max-Coverage.

    Algoritmo:
      A cada passo, escolhe o bilhete que cobre o maior número de dezenas
      ainda não cobertas. Empates são resolvidos pelo menor overlap acumulado
      com os bilhetes já selecionados.

    Fundamento matemático:
      Maximizar a cobertura de {1..25} é equivalente a minimizar a sobreposição
      media entre bilhetes, o que maximiza a independência dos eventos
      "bilhete i tem ≥11 acertos" — diretamente aumentando P(≥11 em algum).

      O algoritmo greedy garante solução ≥ (1 − 1/e) ≈ 63% do ótimo para
      o problema de cobertura máxima (Nemhauser et al., 1978).

    Parameters
    ----------
    pool : ndarray shape (M, 15)
    n    : número de bilhetes a selecionar

    Returns
    -------
    ndarray shape (n, 15)
    """
    M = len(pool)
    # Indicador booleano: (M, 25) — t_bool[i, j] = 1 se dezena j+1 ∈ bilhete i
    t_bool = np.zeros((M, N_UNIVERSE), dtype=np.uint8)
    t_bool[np.repeat(np.arange(M), N_DRAW), pool.ravel() - 1] = 1

    # MULT garante que 1 unidade de ganho de cobertura sempre supera
    # qualquer diferença de overlap acumulado como critério de desempate.
    MULT = n * N_DRAW + 1

    selected: list[int] = []
    covered = np.zeros(N_UNIVERSE, dtype=bool)
    available = np.ones(M, dtype=bool)
    cumulative_overlap = np.zeros(M, dtype=np.int64)

    for _ in range(n):
        gains = t_bool[:, ~covered].sum(axis=1).astype(np.int64)
        score = gains * MULT - cumulative_overlap
        score[~available] = np.iinfo(np.int64).min

        best = int(np.argmax(score))
        selected.append(best)
        covered[pool[best] - 1] = True
        available[best] = False

        # Atualiza overlap acumulado: cada candidato ganha o overlap com o
        # bilhete recém-selecionado.
        cumulative_overlap += (t_bool @ t_bool[best]).astype(np.int64)

    return pool[selected]


# ---------------------------------------------------------------------------
# Módulo 3 — Refinamento por Simulated Annealing (objetivo: overlap mínimo)
# ---------------------------------------------------------------------------

def refine_overlap_sa(
    tickets: np.ndarray,
    rng: np.random.Generator,
    n_iter: int = 8_000,
    T0: float = 2.0,
    cooling: float = 0.9993,
) -> np.ndarray:
    """
    Refina o conjunto de bilhetes minimizando a sobreposição total pareada.

    Objetivo matemático (minimizar):
        Σ_{i<j} |A_i ∩ A_j|   (soma de todas as interseções entre pares)

    Fundamento: sobreposição menor → eventos mais independentes →
    P(≥11 em ao menos um bilhete) maior.

    Implementação eficiente: em vez de recalcular a matriz de sobreposição
    inteira a cada iteração, calcula apenas o delta causado pela mutação
    de um único bilhete — O(n × 25) por passo em vez de O(n² × 25).

    Parameters
    ----------
    tickets : ndarray shape (n, 15)
    rng     : numpy Generator
    n_iter  : iterações de SA
    T0      : temperatura inicial
    cooling : fator de resfriamento multiplicativo por iteração

    Returns
    -------
    ndarray shape (n, 15) — bilhetes com sobreposição total reduzida
    """
    universe = np.arange(1, N_UNIVERSE + 1, dtype=np.int32)
    n = len(tickets)

    current = tickets.copy()
    cur_bool = np.zeros((n, N_UNIVERSE), dtype=np.uint8)
    cur_bool[np.repeat(np.arange(n), N_DRAW), current.ravel() - 1] = 1

    # Objetivo inicial: soma do triângulo superior da matriz de overlap
    overlap_mat = cur_bool @ cur_bool.T
    idx_u = np.triu_indices(n, k=1)
    current_obj = int(overlap_mat[idx_u].sum())

    best = current.copy()
    best_obj = current_obj
    T = T0

    for _ in range(n_iter):
        # Mutação: troca uma dezena de um bilhete aleatório
        ti = int(rng.integers(n))
        t_old = current[ti].copy()
        not_in = np.setdiff1d(universe, t_old, assume_unique=True)

        t_new = t_old.copy()
        t_new[int(rng.integers(N_DRAW))] = rng.choice(not_in)
        t_new = np.sort(t_new)

        # Delta eficiente: apenas os overlaps do bilhete ti com os demais mudam
        others = cur_bool[np.arange(n) != ti]   # (n-1, 25)
        old_b = cur_bool[ti]
        new_b = np.zeros(N_UNIVERSE, dtype=np.uint8)
        new_b[t_new - 1] = 1

        delta = int((others @ new_b).sum()) - int((others @ old_b).sum())

        if delta < 0 or rng.random() < np.exp(-delta / T):
            current[ti] = t_new
            cur_bool[ti] = new_b
            current_obj += delta
            if current_obj < best_obj:
                best = current.copy()
                best_obj = current_obj

        T *= cooling

    return best


# ---------------------------------------------------------------------------
# Módulo 4 — Estimativa Monte Carlo de P(≥11)
# ---------------------------------------------------------------------------

def prob_min11_monte_carlo(
    tickets: np.ndarray,
    num_sim: int,
    rng: np.random.Generator,
    chunk_size: int = 10_000,
) -> float:
    """
    Estima P(ao menos um bilhete com ≥11 acertos) via simulação vetorizada.

    Processa em lotes de chunk_size para controlar uso de memória.
    Complexidade por chunk: O(chunk_size × 25 × n_bilhetes).

    Parameters
    ----------
    tickets    : ndarray shape (n, 15)
    num_sim    : sorteios a simular
    rng        : numpy Generator
    chunk_size : linhas por lote

    Returns
    -------
    float em [0, 1]
    """
    n = len(tickets)
    t_bool = np.zeros((n, N_UNIVERSE), dtype=np.uint8)
    t_bool[np.repeat(np.arange(n), N_DRAW), tickets.ravel() - 1] = 1

    total = 0
    for start in range(0, num_sim, chunk_size):
        sz = min(chunk_size, num_sim - start)

        # Sorteios: argsort de floats uniformes = permutação aleatória uniforme
        draws = (
            rng.random((sz, N_UNIVERSE)).argsort(axis=1)[:, :N_DRAW].astype(np.uint8) + 1
        )
        d_bool = np.zeros((sz, N_UNIVERSE), dtype=np.uint8)
        d_bool[np.repeat(np.arange(sz), N_DRAW), draws.ravel() - 1] = 1

        # hits[i, j] = |sorteio_i ∩ bilhete_j|  →  shape (sz, n)
        hits = d_bool @ t_bool.T
        total += int(np.any(hits >= 11, axis=1).sum())

    return total / num_sim


# ---------------------------------------------------------------------------
# Métricas auxiliares
# ---------------------------------------------------------------------------

def compute_overlap_matrix(tickets: np.ndarray) -> np.ndarray:
    """Matriz (n, n) com o número de dezenas em comum entre cada par de bilhetes."""
    n = len(tickets)
    t_bool = np.zeros((n, N_UNIVERSE), dtype=np.uint8)
    t_bool[np.repeat(np.arange(n), N_DRAW), tickets.ravel() - 1] = 1
    return (t_bool @ t_bool.T).astype(int)


def bucket_entropy(tickets: np.ndarray) -> np.ndarray:
    """
    Entropia de Shannon da distribuição de dezenas de cada bilhete sobre
    5 quintis: {1-5}, {6-10}, {11-15}, {16-20}, {21-25}.

    Máximo = log2(5) ≈ 2.322 (3 dezenas por quintil).
    Mede quão uniformemente o bilhete está distribuído pelo universo.

    (Diferentemente da fórmula com p_i = 1/15, que é constante para todos
    os bilhetes válidos e não discrimina nada.)
    """
    bucket_idx = (tickets - 1) // 5  # mapeia 1-5→0, 6-10→1, ..., 21-25→4
    counts = np.stack([(bucket_idx == b).sum(axis=1) for b in range(5)], axis=1)
    probs = counts.astype(float) / N_DRAW
    log_probs = np.where(probs > 0, np.log2(probs), 0.0)
    return -(probs * log_probs).sum(axis=1)


# ---------------------------------------------------------------------------
# Anti-padrões — ferramenta de análise SEPARADA (não usada na otimização)
# ---------------------------------------------------------------------------

DEFAULT_PESOS_H: dict = {
    "runs_longas": 3.0,
    "concentracao": 2.0,
    "soma": 1.5,
    "paridade": 2.0,
    "multiplos5": 1.0,
    "multiplos3": 0.5,
    "finais_rep": 1.5,
    "datas": 1.0,
}


def score_human_batch(tickets: np.ndarray, pesos: Optional[dict] = None) -> np.ndarray:
    """
    Calcula um score de "popularidade humana" H(A) para cada bilhete.

    AVISO: este score é baseado em suposições qualitativas sobre o comportamento
    de apostadores, SEM a distribuição real das apostas da Lotofácil.
    Não é usado na otimização principal — só como análise exploratória.
    Para ser acionável, precisaria dos dados reais de quais combinações
    são mais apostadas.

    Parameters
    ----------
    tickets : ndarray shape (N, 15)
    pesos   : dicionário de pesos (None → DEFAULT_PESOS_H)

    Returns
    -------
    ndarray shape (N,)  — quanto maior, mais "tipicamente humano"
    """
    if pesos is None:
        pesos = DEFAULT_PESOS_H

    scores = np.zeros(len(tickets), dtype=float)
    diffs = np.diff(tickets, axis=1)

    run4 = (diffs[:, :-2] == 1) & (diffs[:, 1:-1] == 1) & (diffs[:, 2:] == 1)
    scores += pesos["runs_longas"] * run4.any(axis=1)

    in_bottom = (tickets <= 13).sum(axis=1)
    scores += pesos["concentracao"] * ((in_bottom > 10) | (in_bottom < 5))

    sums = tickets.sum(axis=1)
    scores += pesos["soma"] * ((sums < 170) | (sums > 210))

    n_even = (tickets % 2 == 0).sum(axis=1)
    scores += pesos["paridade"] * ((n_even > 10) | (n_even < 5))

    mult5 = (tickets % 5 == 0).sum(axis=1)
    scores += pesos["multiplos5"] * np.maximum(0, mult5 - 3)

    mult3 = (tickets % 3 == 0).sum(axis=1)
    scores += pesos["multiplos3"] * np.maximum(0, mult3 - 5)

    units = tickets % 10
    ending_counts = (units[:, :, None] == np.arange(10)[None, None, :]).sum(axis=1)
    scores += pesos["finais_rep"] * np.maximum(0, ending_counts.max(axis=1) - 2)

    n_dates = (tickets <= 12).sum(axis=1)
    scores += pesos["datas"] * np.maximum(0, n_dates - 8)

    return scores


# ---------------------------------------------------------------------------
# Ponto de entrada principal
# ---------------------------------------------------------------------------

def generate_apostas(
    n_bilhetes: int = 5,
    num_simulacoes: int = 100_000,
    modo_otimizacao: str = "greedy",
    seed: Optional[int] = None,
) -> dict:
    """
    Gera n_bilhetes apostas otimizadas por cobertura combinatória.

    A otimização é puramente matemática:
    - Greedy: maximiza cobertura marginal de {1..25} a cada bilhete adicionado
    - Annealing: refina minimizando sobreposição total pareada Σ|A_i ∩ A_j|
    Ambos maximizam P(≥11 acertos em pelo menos um bilhete).

    Parameters
    ----------
    n_bilhetes      : bilhetes a gerar
    num_simulacoes  : sorteios Monte Carlo para estimar P(≥11)
    modo_otimizacao : "greedy" ou "annealing"
    seed            : semente para reprodutibilidade

    Returns
    -------
    dict com:
        bilhetes            — lista de listas com as dezenas
        probabilidade_>=11  — estimativa Monte Carlo
        prob_referencia     — limite superior teórico (bilhetes independentes)
        cobertura_total     — dezenas distintas cobertas pelo conjunto
        sobreposicao_media  — média de |A_i ∩ A_j| sobre todos os pares
        sobreposicao_total  — Σ|A_i ∩ A_j| (objetivo minimizado)
        entropia_media      — entropia de quintis média (0 a log2(5) ≈ 2.32)
    """
    if modo_otimizacao not in ("greedy", "annealing"):
        raise ValueError(f"modo_otimizacao deve ser 'greedy' ou 'annealing'")

    rng = np.random.default_rng(seed)
    n_pool = max(500, n_bilhetes * 60)

    print(f"[1/3] Gerando pool de {n_pool} candidatos aleatórios...")
    pool = generate_ticket_pool(n_pool, rng)

    print(f"[2/3] Selecionando {n_bilhetes} bilhetes (modo={modo_otimizacao})...")
    selected = greedy_coverage_select(pool, n_bilhetes)

    if modo_otimizacao == "annealing":
        print("      Refinando com SA (minimizando sobreposição pareada)...")
        selected = refine_overlap_sa(selected, rng)

    print(f"[3/3] Simulando {num_simulacoes:,} sorteios (Monte Carlo)...")
    prob = prob_min11_monte_carlo(selected, num_simulacoes, rng)

    overlap = compute_overlap_matrix(selected)
    n = len(selected)
    triu = np.triu_indices(n, k=1)

    return {
        "n_bilhetes": n_bilhetes,
        "bilhetes": [row.tolist() for row in selected],
        "probabilidade_>=11": round(float(prob), 4),
        "prob_referencia": round(prob_minimo_um_bilhete_independente(n_bilhetes), 4),
        "cobertura_total": int(np.unique(selected).size),
        "sobreposicao_media": round(float(overlap[triu].mean()), 2) if n > 1 else 0.0,
        "sobreposicao_total": int(overlap[triu].sum()) if n > 1 else 0,
        "entropia_media": round(float(bucket_entropy(selected).mean()), 4),
    }


# ---------------------------------------------------------------------------
# Visualização
# ---------------------------------------------------------------------------

def plot_results(resultado: dict) -> None:
    """
    Plota três painéis:
    1. Frequência de cada dezena nos bilhetes gerados vs. esperado uniforme.
    2. Matriz de sobreposição entre bilhetes (número de dezenas em comum).
    3. Evolução da cobertura acumulada de {1..25} conforme bilhetes são adicionados.
    """
    tickets = np.array(resultado["bilhetes"])
    n = len(tickets)
    labels = [f"B{i + 1}" for i in range(n)]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # 1. Frequência das dezenas
    axes[0].hist(
        tickets.ravel(),
        bins=np.arange(0.5, N_UNIVERSE + 1.5),
        alpha=0.7,
        edgecolor="black",
        color="steelblue",
    )
    axes[0].axhline(
        n * N_DRAW / N_UNIVERSE,
        color="red",
        linestyle="--",
        label=f"Esperado uniforme ({n * N_DRAW / N_UNIVERSE:.1f})",
    )
    axes[0].set_title("Frequência das dezenas")
    axes[0].set_xlabel("Dezena")
    axes[0].set_ylabel("Frequência")
    axes[0].legend()

    # 2. Matriz de sobreposição
    overlap = compute_overlap_matrix(tickets)
    im = axes[1].imshow(overlap, cmap="YlOrRd", vmin=0, vmax=N_DRAW)
    axes[1].set_title("Sobreposição entre bilhetes\n(dezenas em comum)")
    axes[1].set_xticks(range(n))
    axes[1].set_yticks(range(n))
    axes[1].set_xticklabels(labels)
    axes[1].set_yticklabels(labels)
    for i in range(n):
        for j in range(n):
            axes[1].text(j, i, str(overlap[i, j]), ha="center", va="center", fontsize=9)
    plt.colorbar(im, ax=axes[1], label="Dezenas em comum")

    # 3. Cobertura acumulada
    covered = np.zeros(N_UNIVERSE, dtype=bool)
    cov_evolution = []
    for t in tickets:
        covered[np.array(t) - 1] = True
        cov_evolution.append(int(covered.sum()))

    axes[2].plot(range(1, n + 1), cov_evolution, marker="o", linewidth=2, color="steelblue")
    axes[2].axhline(N_UNIVERSE, color="red", linestyle="--", label="Universo completo (25)")
    axes[2].set_title("Cobertura acumulada de {1..25}")
    axes[2].set_xlabel("Bilhetes adicionados")
    axes[2].set_ylabel("Dezenas distintas cobertas")
    axes[2].set_xticks(range(1, n + 1))
    axes[2].set_ylim(0, N_UNIVERSE + 1)
    axes[2].legend()

    p_mc = resultado["probabilidade_>=11"]
    p_ref = resultado["prob_referencia"]
    plt.suptitle(
        f"P(≥11) estimada = {p_mc:.4f}  |  limite independência = {p_ref:.4f}  |  "
        f"Cobertura = {resultado['cobertura_total']}/25  |  "
        f"Sobreposição total = {resultado['sobreposicao_total']}",
        fontsize=9,
    )
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# __main__ — exemplo de uso
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Referência teórica por bilhete
    probs = prob_por_acertos()
    print("=== REFERÊNCIA TEÓRICA (por bilhete) ===")
    for k, p in probs.items():
        print(f"  P({k} acertos) = {p:.6f}")
    print(f"  P(≥11 acertos) = {sum(probs.values()):.6f}")
    print()

    resultado = generate_apostas(
        n_bilhetes=5,
        num_simulacoes=100_000,
        modo_otimizacao="annealing",
        seed=42,
    )

    print("\n=== APOSTAS GERADAS ===")
    for i, b in enumerate(resultado["bilhetes"]):
        print(f"  B{i + 1}: {b}")

    print(f"\nP(≥11 em algum bilhete) — simulação : {resultado['probabilidade_>=11']:.4f}")
    print(f"P(≥11 em algum bilhete) — ref. teórica: {resultado['prob_referencia']:.4f}")
    print(f"  (diferença = ineficiência por sobreposição forçada)")
    print(f"\nCobertura total     : {resultado['cobertura_total']}/25")
    print(f"Sobreposição média  : {resultado['sobreposicao_media']:.2f} dezenas em comum por par")
    print(f"Sobreposição total  : {resultado['sobreposicao_total']}")
    print(f"Entropia de quintis : {resultado['entropia_media']:.4f}  (máx = {np.log2(5):.4f})")

    plot_results(resultado)
