# -*- coding: utf-8 -*-
"""Estende a verificacao da conjectura (leitura sup, n=3) para v=12 e v=13."""
from math import comb
from collections import defaultdict

def p_num(v, k, t):
    return sum(comb(k, j) * comb(v - k, k - j) for j in range(t, k + 1))

def g_num(v, k, t, m):
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

def g3_num(cells, v, k, t):
    c123, c12, c13, c23, c1, c2, c3, c0 = cells
    tot = 0
    for x123 in range(min(c123, k) + 1):
        for x12 in range(min(c12, k - x123) + 1):
            for x13 in range(min(c13, k - x123 - x12) + 1):
                r1 = k - x123 - x12 - x13
                for x23 in range(min(c23, r1) + 1):
                    r2 = r1 - x23
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

def scan(v, k, t):
    pn = p_num(v, k, t)
    gc = {}
    def G(m):
        if m not in gc:
            gc[m] = g_num(v, k, t, m)
        return gc[m]
    ex = 2 * t - k - 1
    mstar = max(0, 2 * k - v)
    res = {}
    for m12 in range(mstar, k + 1):
        for m13 in range(mstar, k + 1):
            for m23 in range(mstar, k + 1):
                S = m12 + m13 + m23
                lo = max(0, m12 + m13 - k, m12 + m23 - k, m13 + m23 - k)
                hi = min(m12, m13, m23, v - 3 * k + S)
                for c123 in range(lo, hi + 1):
                    cells = (c123, m12 - c123, m13 - c123, m23 - c123,
                             k - m12 - m13 + c123, k - m12 - m23 + c123,
                             k - m13 - m23 + c123, v - 3 * k + S - c123)
                    if any(c < 0 for c in cells):
                        continue
                    g3 = 0 if min(m12, m13, m23) <= ex else g3_num(cells, v, k, t)
                    res[(m12, m13, m23, c123)] = 3 * pn - (G(m12) + G(m13) + G(m23)) + g3
    return res

def check_sup(res):
    sup = defaultdict(lambda: -1)
    for (a, b, c, _), n_ in res.items():
        if n_ > sup[(a, b, c)]:
            sup[(a, b, c)] = n_
    out = []
    for (a, b, c), n_ in sup.items():
        for prof in [(a + 1, b, c), (a, b + 1, c), (a, b, c + 1)]:
            if prof in sup and sup[prof] > n_:
                out.append(((a, b, c), prof))
    return out

total = 0
for v in (12, 13):
    for k in range(2, v):
        for t in range(1, k + 1):
            if p_num(v, k, t) == 0:
                continue
            vv = check_sup(scan(v, k, t))
            if vv:
                total += 1
                print(f"(v={v},k={k},t={t}): {len(vv)} violacoes SUP; ex {vv[0]}")
print(f"famipias (v,k,t) com v in {{12,13}} com violacao SUP (n=3): {total}")
