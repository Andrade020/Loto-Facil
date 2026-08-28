# -*- coding: utf-8 -*-
"""Valida o LEMA novo (troca preservadora de padrao):
   se A2' = A2 - y + x com x em A1\\A2, y em A2\\A1 e 1[x in Aj] = 1[y in Aj]
   para todo j >= 3, entao
   Pwin(A1,A2',A3..) - Pwin(A1,A2,A3..) =
       -P(S1 = t, W = t-1, todos os outros falham, x in R, y notin R) <= 0.
   Verificacao exata por forca bruta em universos pequenos, n=3 e n=4."""
import random
from itertools import combinations

rng = random.Random(2026)

def pwin_and_delta(v, k, t, tickets, i_mod, x, y):
    """retorna (wins_antes, wins_depois, rhs) como contagens inteiras"""
    A = [frozenset(s) for s in tickets]
    A2 = A[i_mod]
    A2p = frozenset((A2 - {y}) | {x})
    Ap = list(A); Ap[i_mod] = A2p
    wins_b = wins_a = rhs = 0
    A1 = A[0]
    others = [A[j] for j in range(len(A)) if j not in (0, i_mod)]
    for Rt in combinations(range(v), k):
        R = frozenset(Rt)
        if any(len(a & R) >= t for a in A):
            wins_b += 1
        if any(len(a & R) >= t for a in Ap):
            wins_a += 1
        if (len(A1 & R) == t and len(A2 & R) == t - 1 and x in R and y not in R
                and all(len(o & R) < t for o in others)):
            rhs += 1
    return wins_b, wins_a, rhs

bad = 0
tested = 0
for trial in range(400):
    v = rng.randint(7, 11)
    k = rng.randint(2, v - 2)
    t = rng.randint(1, k)
    n = rng.choice([3, 4])
    tickets = [rng.sample(range(v), k) for _ in range(n)]
    A = [set(s) for s in tickets]
    # i_mod = 1 (A2); acha (x,y) com mesmo padrao nos demais
    cands = []
    for x in A[0] - A[1]:
        for y in A[1] - A[0]:
            if all((x in A[j]) == (y in A[j]) for j in range(n) if j not in (0, 1)):
                cands.append((x, y))
    if not cands:
        continue
    x, y = rng.choice(cands)
    wb, wa, rhs = pwin_and_delta(v, k, t, tickets, 1, x, y)
    tested += 1
    if wa - wb != -rhs or wa > wb:
        bad += 1
        print("FALHA:", v, k, t, n, tickets, x, y, wb, wa, rhs)
print(f"casos testados: {tested} (n=3 e n=4, v em 7..11), falhas: {bad}")
print("identidade Delta = -P(S1=t, W=t-1, outros falham, x in R, y notin R): OK" if bad == 0 else "REFUTADO")
