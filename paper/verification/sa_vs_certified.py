# -*- coding: utf-8 -*-
"""O greedy+SA atinge os otimos certificados para n=3..6?
Pwin exato por forca bruta sobre os C(25,15) sorteios."""
import sys
from itertools import combinations
import numpy as np

sys.path.insert(0, r"C:\Users\LucasRafaeldeAndrade\Desktop\Repositorios\Loto-Facil")
from lotofacil_optimizer import (generate_ticket_pool, greedy_coverage_select,
                                 refine_overlap_sa)

V, K, T = 25, 15, 11
OPT = {3: 1028578, 4: 1322189, 5: 1626630, 6: 1840731}
DEN = 3268760

# pre-gera todos os sorteios como mascaras de bits
draws = np.fromiter(
    (sum(1 << e for e in c) for c in combinations(range(V), K)),
    dtype=np.int64, count=DEN)
print(f"sorteios pre-computados: {len(draws)}")

POPC = np.array([bin(i).count("1") for i in range(1 << 16)], dtype=np.int8)
def popcount(a):
    return (POPC[a & 0xFFFF].astype(np.int16) + POPC[(a >> 16) & 0xFFFF])

def pwin_exact(tickets):
    """tickets: lista de listas de numeros 1..25"""
    wins = np.zeros(len(draws), dtype=bool)
    for tk in tickets:
        mask = sum(1 << (e - 1) for e in tk)
        wins |= popcount(draws & mask) >= T
    return int(wins.sum())

print(f"{'n':>2} {'seeds':>6} {'melhor SA':>12} {'otimo':>10} {'atinge?':>9}  perfil")
for n in (3, 4, 5, 6):
    best, best_prof, nhit = -1, None, 0
    for seed in range(10):
        rng = np.random.default_rng(seed)
        pool = generate_ticket_pool(500, rng)
        sa = refine_overlap_sa(greedy_coverage_select(pool, n), rng, n_iter=2000)
        tk = [sorted(map(int, row)) for row in sa]
        val = pwin_exact(tk)
        sets = [set(x) for x in tk]
        prof = tuple(sorted(len(sets[i] & sets[j])
                            for i in range(n) for j in range(i + 1, n)))
        if val == OPT[n]:
            nhit += 1
        if val > best:
            best, best_prof = val, prof
    print(f"{n:>2} {nhit:>3}/10 {best:>12} {OPT[n]:>10} "
          f"{'SIM' if best == OPT[n] else 'NAO':>9}  {best_prof}")
