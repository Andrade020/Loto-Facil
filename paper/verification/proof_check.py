# -*- coding: utf-8 -*-
"""Valida a identidade da prova por bijecao de troca (swap coupling):
   g(m+1) - g(m) = P(|A1 cap R| = t, |A2 cap R| = t-1, x in R, y not in R)
   com x em A1\\A2, y em A2\\A1, overlap(A1,A2)=m.
   Particao refinada: S0(m), S1'=(k-m-1), {x}, S2'=(k-m-1), {y}, S3(v-2k+m)."""
from math import comb

def g_num(v, k, t, m):
    s0, s1, s2, s3 = m, k - m, k - m, v - 2 * k + m
    tot = 0
    for x0 in range(min(s0, k) + 1):
        for x1 in range(min(s1, k - x0) + 1):
            if x0 + x1 < t:
                continue
            rem = k - x0 - x1
            for x2 in range(max(0, t - x0), min(s2, rem) + 1):
                x3 = rem - x2
                if 0 <= x3 <= s3:
                    tot += comb(s0, x0) * comb(s1, x1) * comb(s2, x2) * comb(s3, x3)
    return tot

def rhs_num(v, k, t, m):
    """P(S1cnt=t, W=t-1, x in R, y notin R) * C(v,k):
       x conta em A1; y fora de R. Componentes: X0 de S0, X1p de S1'(k-m-1),
       x incluido, X2p de S2'(k-m-1), X3 de S3.
       |A1 cap R| = X0+X1p+1 = t ; |A2 cap R| = X0+X2p = t-1
       tamanho: X0+X1p+1+X2p+X3 = k"""
    s0, s1p, s2p, s3 = m, k - m - 1, k - m - 1, v - 2 * k + m
    tot = 0
    for x0 in range(min(s0, k) + 1):
        x1p = t - 1 - x0          # de X0+X1p = t-1
        x2p = t - 1 - x0
        if not (0 <= x1p <= s1p and 0 <= x2p <= s2p):
            continue
        x3 = k - 1 - x0 - x1p - x2p
        if 0 <= x3 <= s3:
            tot += comb(s0, x0) * comb(s1p, x1p) * comb(s2p, x2p) * comb(s3, x3)
    return tot

print("Lotofacil (25,15,11):")
for m in range(5, 15):
    d_real = g_num(25, 15, 11, m + 1) - g_num(25, 15, 11, m)
    d_form = rhs_num(25, 15, 11, m)
    print(f"  m={m:2d}: g(m+1)-g(m) = {d_real:>12d}   formula = {d_form:>12d}   ok={d_real == d_form}")

print()
print("Varredura geral v<=16 (todas k,t,m):")
bad = 0
tested = 0
for v in range(3, 17):
    for k in range(1, v):
        for t in range(1, k + 1):
            for m in range(max(0, 2 * k - v), k):
                tested += 1
                if g_num(v, k, t, m + 1) - g_num(v, k, t, m) != rhs_num(v, k, t, m):
                    bad += 1
                    print("  FALHA:", v, k, t, m)
print(f"testados: {tested}, falhas: {bad}")
