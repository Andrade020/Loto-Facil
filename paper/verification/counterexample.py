# -*- coding: utf-8 -*-
"""1) Contraexemplo explicito da Conjectura 3.11 em (v,k,t)=(11,7,4), n=3,
   verificado por forca bruta sobre TODOS os C(11,7)=330 sorteios.
   2) MC de um desenho balanceado n=5 para a Lotofacil vs numero do paper."""
from itertools import combinations
from math import comb
from fractions import Fraction

V, K, T = 11, 7, 4

def pwin_bruteforce(tickets, v, k, t):
    wins = 0
    tot = 0
    tsets = [frozenset(x) for x in tickets]
    for R in combinations(range(v), k):
        Rs = set(R)
        tot += 1
        if any(len(A & Rs) >= t for A in tsets):
            wins += 1
    return Fraction(wins, tot)

# --- Colecao A: overlaps (5,5,5), c123=5 ---
# nucleo C={0,1,2,3,4}; unicos: A1 +{5,6}, A2 +{7,8}, A3 +{9,10}
C = [0, 1, 2, 3, 4]
A = [C + [5, 6], C + [7, 8], C + [9, 10]]

# --- Colecao B: overlaps (6,5,5) ---
# celulas c123=4: c12=2, c13=1, c23=1, c1=0, c2=0, c3=1, c0=2
# nucleo triplo {0,1,2,3}; c12={4,5}; c13={6}; c23={7}; c3={8}; c0={9,10}
B1 = [0, 1, 2, 3] + [4, 5] + [6]        # 123 + 12 + 13
B2 = [0, 1, 2, 3] + [4, 5] + [7]        # 123 + 12 + 23
B3 = [0, 1, 2, 3] + [6] + [7] + [8]     # 123 + 13 + 23 + 3
B = [B1, B2, B3]

def overlaps(ts):
    s = [set(x) for x in ts]
    return (len(s[0] & s[1]), len(s[0] & s[2]), len(s[1] & s[2]),
            len(s[0] & s[1] & s[2]))

print(f"(v,k,t)=({V},{K},{T})  m*={max(0,2*K-V)}")
print(f"A: overlaps (m12,m13,m23,c123) = {overlaps(A)}")
pa = pwin_bruteforce(A, V, K, T)
print(f"   Pwin(A) = {pa} = {float(pa):.6f}")
print(f"B: overlaps (m12,m13,m23,c123) = {overlaps(B)}")
pb = pwin_bruteforce(B, V, K, T)
print(f"   Pwin(B) = {pb} = {float(pb):.6f}")
print(f"m12 aumentou 5->6 com m13,m23 fixos; Pwin AUMENTOU? {pb > pa}")

# todas as variantes de (5,5,5) por c123 (3,4,5) para leitura 'forte'
print()
print("Todas as realizacoes de perfil (5,5,5):")
# c123=3: c12=c13=c23=2, c1=c2=c3=7-10+3=0, c0=11-21+15-3=2
V555 = {
    3: [[0,1,2]+[3,4]+[5,6], [0,1,2]+[3,4]+[7,8], [0,1,2]+[5,6]+[7,8]],
    # c123=4: c12=c13=c23=1, c1=c2=c3=7-10+4=1, c0=11-21+15-4=1
    4: [[0,1,2,3]+[4]+[5]+[6], [0,1,2,3]+[4]+[7]+[8], [0,1,2,3]+[5]+[7]+[9]],
    5: A,
}
best555 = 0
for c123, ts in V555.items():
    ov = overlaps(ts)
    assert ov[:3] == (5, 5, 5) and ov[3] == c123, ov
    pw = pwin_bruteforce(ts, V, K, T)
    best555 = max(best555, pw)
    print(f"  c123={c123}: Pwin = {pw} = {float(pw):.6f}")
print(f"MELHOR (5,5,5) = {float(best555):.6f}  <  Pwin(B)(6,5,5) = {float(pb):.6f} ?  {best555 < pb}")

# ------------------------------------------------------------------
print()
print("=" * 70)
print("Desenho balanceado n=5 (Lotofacil) vs paper SA=0.4756")
print("=" * 70)
import numpy as np
# incidencia 5x25: cada elemento pertence a exatamente 3 dos 5 bilhetes
pats = list(combinations(range(5), 3))          # 10 padroes
cols = pats * 2 + [(i, (i+1) % 5, (i+2) % 5) for i in range(5)]  # 25 colunas
assert len(cols) == 25
tickets = np.zeros((5, 25), dtype=np.float32)
for e, patt in enumerate(cols):
    for i in patt:
        tickets[i, e] = 1.0
assert (tickets.sum(axis=1) == 15).all()
ovm = (tickets @ tickets.T).astype(int)
print("overlaps m_ij:", sorted(ovm[np.triu_indices(5, 1)]))

rng = np.random.default_rng(42)
ND, wins = 2_000_000, 0
for _ in range(100):
    chunk = 20_000
    draws = np.zeros((chunk, 25), dtype=np.float32)
    idx = rng.permuted(np.tile(np.arange(25), (chunk, 1)), axis=1)[:, :15]
    np.put_along_axis(draws, idx, 1.0, axis=1)
    cnt = draws @ tickets.T
    wins += int(((cnt >= 11).any(axis=1)).sum())
pw5 = wins / ND
se = (pw5 * (1 - pw5) / ND) ** 0.5
print(f"Pwin(design balanceado, n=5) = {pw5:.5f} +- {1.96*se:.5f}   paper SA: 0.4756+-0.0018   U_5 = {1-(1-346126/3268760)**5:.5f}")
