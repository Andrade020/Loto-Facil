# -*- coding: utf-8 -*-
"""Verificacao INDEPENDENTE dos contraexemplos n=4 (sem dict de permutacoes):
   para (v,k,t) e dois perfis-alvo (como multiconjuntos de 6 overlaps),
   varre todas as colecoes, calcula max Pwin por perfil e exibe argmax."""
from itertools import combinations, combinations_with_replacement

def max_for_profiles(v, k, t, prof_a, prof_b):
    tickets = list(combinations(range(v), k))
    T = len(tickets)
    sets = [frozenset(x) for x in tickets]
    draws = sets
    win = [[len(a & d) >= t for d in draws] for a in sets]
    pa = tuple(sorted(prof_a)); pb = tuple(sorted(prof_b))
    best = {pa: (-1, None), pb: (-1, None)}
    for c in combinations_with_replacement(range(T), 4):
        s = [sets[i] for i in c]
        prof = tuple(sorted(len(s[i] & s[j]) for i in range(4) for j in range(i + 1, 4)))
        if prof not in best:
            continue
        w = sum(1 for d in range(T)
                if win[c[0]][d] or win[c[1]][d] or win[c[2]][d] or win[c[3]][d])
        if w > best[prof][0]:
            best[prof] = (w, [sorted(x) for x in s])
    den = T
    for p, (w, col) in best.items():
        print(f"  perfil {p}: max wins = {w}/{den}")
        print(f"    argmax: {col}")
    return best[pa][0], best[pb][0]

print("=== (v=9, k=3, t=2): perfil (1,2,2,2,2,2) vs (2,2,2,2,2,2) ===")
wa, wb = max_for_profiles(9, 3, 2, (1,2,2,2,2,2), (2,2,2,2,2,2))
print(f"  VIOLACAO (aumentar overlap 1->2 melhora o sup)? {wb > wa}")
print()
print("=== (v=9, k=4, t=3): perfil (0,0,0,3,3,3) vs (0,0,1,3,3,3) ===")
wa, wb = max_for_profiles(9, 4, 3, (0,0,0,3,3,3), (0,0,1,3,3,3))
print(f"  VIOLACAO (aumentar overlap 0->1 melhora o sup)? {wb > wa}")
