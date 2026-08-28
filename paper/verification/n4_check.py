# -*- coding: utf-8 -*-
"""Testa a conjectura de monotonicidade de perfil (leitura sup) para n=4,
   por enumeracao EXATA de todas as colecoes de 4 bilhetes em universos
   pequenos. F(perfil de 6 overlaps) = max wins; checa se F e nao-crescente
   em cada coordenada (comparando perfis ordenados via permutacoes)."""
from itertools import combinations, combinations_with_replacement, permutations

def run(v, k, t):
    tickets = list(combinations(range(v), k))
    T = len(tickets)
    masks = [sum(1 << e for e in tk) for tk in tickets]
    # matriz de overlap e vitorias (bit d = 1 se bilhete vence no sorteio d)
    ov = [[bin(masks[i] & masks[j]).count("1") for j in range(T)] for i in range(T)]
    winbits = []
    for i in range(T):
        b = 0
        for d in range(T):  # sorteios = mesmos k-subconjuntos
            if ov[i][d] >= t:
                b |= 1 << d
        winbits.append(b)

    F = {}  # perfil ordenado (m12,m13,m14,m23,m24,m34) -> max wins
    for c in combinations_with_replacement(range(T), 4):
        i, j, l, m = c
        w = bin(winbits[i] | winbits[j] | winbits[l] | winbits[m]).count("1")
        prof = (ov[i][j], ov[i][l], ov[i][m], ov[j][l], ov[j][m], ov[l][m])
        # registra todas as 24 permutacoes (F e invariante por permutacao)
        idx = ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))
        for perm in permutations(range(4)):
            pm = [[0]*4 for _ in range(4)]
            src = (i, j, l, m)
            arr = [src[perm[0]], src[perm[1]], src[perm[2]], src[perm[3]]]
            p = tuple(ov[arr[a]][arr[b]] for a, b in idx)
            if F.get(p, -1) < w:
                F[p] = w
    viol = []
    for prof, w in F.items():
        for i in range(6):
            p2 = list(prof); p2[i] += 1; p2 = tuple(p2)
            if p2 in F and F[p2] > w:
                viol.append((prof, p2, w, F[p2]))
    den = len(tickets)
    print(f"(v={v},k={k},t={t}): {len(F)} perfis ordenados, "
          f"violacoes SUP = {len(viol)}")
    for x in viol[:5]:
        print(f"   {x[0]} (F={x[2]}/{den}) -> {x[1]} (F={x[3]}/{den})")
    return len(viol)

total = 0
for v, k, t in [(7,3,1),(7,3,2),(7,3,3),(8,3,2),(8,4,2),(8,4,3),(8,4,4),(9,4,3),(9,3,2)]:
    total += run(v, k, t)
print(f"\nTOTAL de violacoes da leitura SUP em n=4: {total}")
