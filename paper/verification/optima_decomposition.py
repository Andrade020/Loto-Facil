# -*- coding: utf-8 -*-
"""Confere a decomposicao Pwin = n*p - sum g + sum g3 (ordens >=4 nulas)
para os quatro otimos certificados, em aritmetica inteira exata."""
from math import comb

V, K, T = 25, 15, 11
DEN = comb(V, K)
PN = sum(comb(K, j) * comb(V - K, K - j) for j in range(T, K + 1))

def g_num(m):
    s0, s1, s2, s3 = m, K - m, K - m, V - 2 * K + m
    if s3 < 0 or m <= 2 * T - K - 1:
        return 0
    tot = 0
    for x0 in range(min(s0, K) + 1):
        for x1 in range(min(s1, K - x0) + 1):
            if x0 + x1 < T:
                continue
            rem = K - x0 - x1
            for x2 in range(max(0, T - x0), min(s2, rem) + 1):
                x3 = rem - x2
                if 0 <= x3 <= s3:
                    tot += comb(s0, x0) * comb(s1, x1) * comb(s2, x2) * comb(s3, x3)
    return tot

G = {m: g_num(m) for m in range(16)}

cases = [
    ("n=3", 3, [7, 7, 6], 0, 1028578),
    ("n=4", 4, [8, 8, 8, 7, 7, 7], 160, 1322189),          # 1 triangulo (8,8,8) T3=4
    ("n=5", 5, [8]*5 + [7]*5, 5 * 25, 1626630),            # 5 triplas (8,8,7) T3=3
    ("n=6", 6, [8]*15, 10 * 160 + 10 * 125, 1840731),      # 10 T3=4 + 10 T3=3
]
print(f"p = {PN}/{DEN}")
for name, n, prof, sum_g3, opt in cases:
    base = n * PN - sum(G[m] for m in prof)
    print(f"{name}: n*p - sum g = {base};  + sum g3 = {sum_g3}  ->  {base + sum_g3}"
          f"   (otimo certificado = {opt})   "
          f"{'CONFERE' if base + sum_g3 == opt else 'DIVERGE!'}")
    print(f"      sum g = {sum(G[m] for m in prof)},  Pwin = {opt/DEN:.6f}")

# n=6: Sigma T3 = 70 com 20 triplas e valores em [1,4]; max de Sigma g3?
print("\nn=6: maximizar sum g3 sujeito a sum T3 = 70, 20 triplas, T3 em [1,4]")
g3v = {1: 0, 2: 0, 3: 125, 4: 160}
best, arg = -1, None
for n4 in range(21):
    for n3 in range(21 - n4):
        for n2 in range(21 - n4 - n3):
            n1 = 20 - n4 - n3 - n2
            if n1 < 0:
                continue
            if 4*n4 + 3*n3 + 2*n2 + n1 != 70:
                continue
            s = 160*n4 + 125*n3
            if s > best:
                best, arg = s, (n4, n3, n2, n1)
print(f"  maximo de sum g3 = {best} com (n4,n3,n2,n1) = {arg}")
print(f"  valor otimo usa sum g3 = 2850 -> {'consistente' if best == 2850 else 'INCONSISTENTE'}")
