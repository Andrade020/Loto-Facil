# -*- coding: utf-8 -*-
"""Verificacao do paper Lotofacil: tabelas exatas, Prop 3.10, Teorema 3.4,
Conjectura 3.11 (n>=3) e baseline aleatoria."""
from math import comb
import sys, itertools, random

V, K, T = 25, 15, 11
DEN = comb(V, K)

# ---------- exact p and pairwise g ----------
def p_num(v, k, t):
    return sum(comb(k, j) * comb(v - k, k - j) for j in range(t, k + 1))

def g_num(v, k, t, m):
    """numerator of P(both tickets >= t) at overlap m (over comb(v,k))"""
    s0, s1, s2, s3 = m, k - m, k - m, v - 2 * k + m
    if s3 < 0:
        return None
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

print("=" * 78)
print("A) Tabela 3.5 do paper: g(m) exato, Lotofacil (25,15,11)")
print("=" * 78)
pn = p_num(V, K, T)
p = pn / DEN
print(f"p = {pn}/{DEN} = {p:.6f}   (paper: 346126/3268760 ~ 0.105889)")
gvals = {}
for m in range(5, 16):
    gn = g_num(V, K, T, m)
    gvals[m] = gn
    print(f"  m={m:2d}  g(m)={gn/DEN:.6f}   Pwin=2p-g={2*p - gn/DEN:.6f}")

print()
print("=" * 78)
print("B) Proposicao 3.10 (upper bound exponencial) -- teste n=2, m=5")
print("=" * 78)
import math
g5 = gvals[5] / DEN
cov = g5 - p * p          # Cov(1_E1, 1_E2)
lhs = 1 - (2 * p - g5)    # 1 - Pwin  (exato)
rhs = (1 - p) ** 2 * math.exp(cov / p**2)
print(f"  1-Pwin (exato)        = {lhs:.6f}")
print(f"  bound da Prop. 3.10   = {rhs:.6f}")
print(f"  bound violado?        = {lhs > rhs}")

print()
print("=" * 78)
print("C) Monotonicidade de g(m) (Teo. 3.4) exaustiva, v<=18 (aritmetica exata)")
print("=" * 78)
viol, ties = [], []
for v in range(3, 19):
    for k in range(1, v):
        for t in range(1, k + 1):
            mstar = max(0, 2 * k - v)
            prev = None
            for m in range(mstar, k + 1):
                gn = g_num(v, k, t, m)
                if prev is not None:
                    if gn < prev:
                        viol.append((v, k, t, m))
                    if m == mstar + 1 and gn == prev:
                        ties.append((v, k, t))
                prev = gn
print(f"  violacoes de g(m+1)>=g(m): {len(viol)}")
if viol:
    print("   exemplos:", viol[:10])
print(f"  casos com g(m*)=g(m*+1) (refutam 'uniquely maximised'): {len(ties)}")
print("   exemplos:", ties[:8], "... inclui (25,15,11)? ->", end=" ")
print(g_num(25, 15, 11, 5) == g_num(25, 15, 11, 6) == 0)

# ---------- triple joint win g3 from Venn cells ----------
def g3_num(cells, v, k, t):
    """cells = (c123,c12,c13,c23,c1,c2,c3,c0); numerator of P(all three >= t)."""
    c123, c12, c13, c23, c1, c2, c3, c0 = cells
    tot = 0
    for x123 in range(min(c123, k) + 1):
        for x12 in range(min(c12, k - x123) + 1):
            for x13 in range(min(c13, k - x123 - x12) + 1):
                r1 = k - x123 - x12 - x13
                lo23_t2 = 0
                for x23 in range(min(c23, r1) + 1):
                    r2 = r1 - x23
                    # ticket1 needs x1 >= t - (x123+x12+x13)
                    lo1 = max(0, t - x123 - x12 - x13)
                    if lo1 > min(c1, r2):
                        continue
                    w0 = comb(c123, x123) * comb(c12, x12) * comb(c13, x13) * comb(c23, x23)
                    for x1 in range(lo1, min(c1, r2) + 1):
                        r3 = r2 - x1
                        lo2 = max(0, t - x123 - x12 - x23)
                        if lo2 > min(c2, r3):
                            continue
                        w1 = w0 * comb(c1, x1)
                        for x2 in range(lo2, min(c2, r3) + 1):
                            r4 = r3 - x2
                            lo3 = max(0, t - x123 - x13 - x23)
                            if lo3 > min(c3, r4):
                                continue
                            w2 = w1 * comb(c2, x2)
                            for x3 in range(lo3, min(c3, r4) + 1):
                                x0 = r4 - x3
                                if 0 <= x0 <= c0:
                                    tot += w2 * comb(c3, x3) * comb(c0, x0)
    return tot

def enum_triple_configs(v, k):
    """yield (m12,m13,m23,c123, cells) for all feasible 3-ticket Venn profiles"""
    mstar = max(0, 2 * k - v)
    for m12 in range(mstar, k + 1):
        for m13 in range(mstar, k + 1):
            for m23 in range(mstar, k + 1):
                S = m12 + m13 + m23
                lo = max(0, m12 + m13 - k, m12 + m23 - k, m13 + m23 - k, 3 * k - S - v + S - ((3*k) - v) if False else 0)
                lo = max(0, m12 + m13 - k, m12 + m23 - k, m13 + m23 - k)
                hi = min(m12, m13, m23, v - 3 * k + S)
                for c123 in range(lo, hi + 1):
                    cells = (c123, m12 - c123, m13 - c123, m23 - c123,
                             k - m12 - m13 + c123, k - m12 - m23 + c123,
                             k - m13 - m23 + c123,
                             v - 3 * k + S - c123)
                    if all(c >= 0 for c in cells):
                        yield (m12, m13, m23, c123, cells)

def scan_triples(v, k, t, verbose_name=""):
    den = comb(v, k)
    pn_ = p_num(v, k, t)
    gcache = {}
    def G(m):
        if m not in gcache:
            gcache[m] = g_num(v, k, t, m)
        return gcache[m]
    excl_thresh = 2 * t - k - 1   # pairwise m <= this => pair jointly exclusive
    results = {}
    for m12, m13, m23, c123, cells in enum_triple_configs(v, k):
        if min(m12, m13, m23) <= excl_thresh:
            g3 = 0
        else:
            g3 = g3_num(cells, v, k, t)
        num = 3 * pn_ - (G(m12) + G(m13) + G(m23)) + g3
        results[(m12, m13, m23, c123)] = num
    return results, den

print()
print("=" * 78)
print("D) Conjectura 3.11 para n=3, Lotofacil (25,15,11): enumeracao EXATA")
print("=" * 78)
res, den = scan_triples(V, K, T)
print(f"  configuracoes viaveis (m12,m13,m23,c123): {len(res)}")

best = max(res.items(), key=lambda kv: kv[1])
worst_minov = None
print(f"  OTIMO GLOBAL: perfil {best[0]}  Pwin = {best[1]/den:.6f}")
tops = sorted(res.items(), key=lambda kv: -kv[1])[:8]
for kk, vv in tops:
    print(f"    {kk}  Pwin={vv/den:.6f}")
# configs de referencia
def show(m12, m13, m23):
    subset = {c: n for (a, b, c2, c), n in [] }
    vals = [(c123, n) for (a, b, c, c123), n in res.items() if (a, b, c) == (m12, m13, m23)]
    for c123, n in sorted(vals):
        print(f"    ({m12},{m13},{m23}) c123={c123}: Pwin={n/den:.6f}")
print("  Perfis de overlap-minimo total (Omega=20):")
show(5, 5, 10); show(6, 6, 8); show(5, 7, 8); show(7, 7, 6); show(6, 7, 7)

# ill-posedness: mesmo (m12,m13,m23), Pwin diferente
from collections import defaultdict
byprof = defaultdict(list)
for (a, b, c, c123), n in res.items():
    byprof[(a, b, c)].append(n)
illposed = [(prof, min(ns), max(ns)) for prof, ns in byprof.items() if min(ns) != max(ns)]
illposed.sort(key=lambda x: -(x[2] - x[1]))
print(f"  perfis (m12,m13,m23) com Pwin NAO determinado pelos overlaps: {len(illposed)}")
for prof, lo, hi in illposed[:5]:
    print(f"    {prof}: Pwin varia de {lo/den:.6f} a {hi/den:.6f} (delta={(hi-lo)/den:.6f})")

# strict monotonicity violations (literal claim)
def find_violations(res, den):
    out = []
    for (a, b, c, c123), n in res.items():
        for idx in range(3):
            prof2 = [a, b, c]
            prof2[idx] += 1
            vals2 = [n2 for (a2, b2, c2, cc), n2 in res.items()
                     if (a2, b2, c2) == tuple(prof2)]
            for n2 in vals2:
                if n2 > n:
                    out.append(((a, b, c, c123), tuple(prof2), (n2 - n) / den, n / den, n2 / den))
    return out

viol3 = find_violations(res, den)
viol3.sort(key=lambda x: -x[2])
print(f"  VIOLACOES ESTRITAS da monotonicidade (aumentar um m_ij aumenta Pwin): {len(viol3)}")
for v_ in viol3[:6]:
    print(f"    {v_[0]} -> perfil {v_[1]}: Pwin {v_[3]:.6f} -> {v_[4]:.6f} (+{v_[2]:.6f})")

print()
print("=" * 78)
print("E) Busca de violacoes estritas em universos pequenos (n=3)")
print("=" * 78)
found = []
for v in range(5, 12):
    for k in range(2, v):
        for t in range(1, k + 1):
            if p_num(v, k, t) == 0:
                continue
            r, d = scan_triples(v, k, t)
            if not r:
                continue
            vv = find_violations(r, d)
            if vv:
                vv.sort(key=lambda x: -x[2])
                found.append((v, k, t, len(vv), vv[0]))
for f in found[:15]:
    v, k, t, nv, ex = f
    print(f"  (v={v},k={k},t={t}): {nv} violacoes; ex: {ex[0]} -> {ex[1]}  "
          f"Pwin {ex[3]:.5f} -> {ex[4]:.5f} (+{ex[2]:.5f})")
print(f"  total de (v,k,t) com violacao estrita: {len(found)}")

print()
print("=" * 78)
print("F) Baseline aleatoria: exato (n=2) e MC (n=3,5)")
print("=" * 78)
# n=2 exato
ov_den = comb(V, K)
Eg = sum(comb(K, m) * comb(V - K, K - m) * gvals[m] for m in range(5, 16)) / (ov_den * DEN)
print(f"  E[g(M)] random = {Eg:.6f}  (p^2 = {p*p:.6f})")
E2 = 2 * p - Eg
U2 = 1 - (1 - p) ** 2
print(f"  E[Pwin] n=2 random EXATO = {E2:.6f}   paper: 0.1997   U_2 = {U2:.6f}")

# n=3 MC sobre trincas aleatorias, Pwin exato por trinca
rng = random.Random(123)
tot3 = 0.0
NS = 400
for s in range(NS):
    A1 = set(rng.sample(range(V), K)); A2 = set(rng.sample(range(V), K)); A3 = set(rng.sample(range(V), K))
    c123 = len(A1 & A2 & A3)
    m12, m13, m23 = len(A1 & A2), len(A1 & A3), len(A2 & A3)
    cells = (c123, m12 - c123, m13 - c123, m23 - c123,
             K - m12 - m13 + c123, K - m12 - m23 + c123, K - m13 - m23 + c123,
             V - 3 * K + m12 + m13 + m23 - c123)
    g3 = 0 if min(m12, m13, m23) <= 6 else g3_num(cells, V, K, T)
    num = 3 * pn - (gvals[m12] + gvals[m13] + gvals[m23]) + g3
    tot3 += num / DEN
E3 = tot3 / NS
U3 = 1 - (1 - p) ** 3
print(f"  E[Pwin] n=3 random (MC exato por trinca, {NS} trincas) = {E3:.6f}   paper: 0.2878   U_3 = {U3:.6f}")

# n=5 e n=7 random via MC puro (numpy)
try:
    import numpy as np
    nprng = np.random.default_rng(7)
    ND = 200_000
    draws = np.zeros((ND, V), dtype=np.float32)
    for i in range(ND):
        draws[i, nprng.choice(V, K, replace=False)] = 1.0
    for n_t, paper_val in [(5, 0.4285), (7, 0.5463)]:
        NC = 200
        tickets = np.zeros((V, n_t * NC), dtype=np.float32)
        for c in range(NC):
            for j in range(n_t):
                tickets[nprng.choice(V, K, replace=False), c * n_t + j] = 1.0
        wins = np.zeros(NC)
        for lo in range(0, ND, 20_000):
            cnt = draws[lo:lo + 20_000] @ tickets           # (chunk, n_t*NC)
            cnt = cnt.reshape(-1, NC, n_t)
            wins += (cnt >= T).any(axis=2).sum(axis=0)
        pw = wins / ND
        Un = 1 - (1 - p) ** n_t
        print(f"  E[Pwin] n={n_t} random (MC, {NC} colecoes x {ND} sorteios) = {pw.mean():.4f} "
              f"+- {1.96*pw.std(ddof=1)/NC**0.5:.4f}   paper: {paper_val}   U_{n_t} = {Un:.4f}")
except ImportError:
    print("  numpy indisponivel; pulei n=5,7")
print()
print("OK")
