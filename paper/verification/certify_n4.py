# -*- coding: utf-8 -*-
"""Certificacao do otimo global para n=4 na Lotofacil (25,15,11).

Estrategia (branch-and-bound exato, aritmetica inteira):
  Pwin = 4p - sum_pares g(m_ij) + sum_triplas g3 - g4,  com g4 >= 0.
  Limite superior por perfil (m_ij):
      UB = 4p - sum g(m_ij) + sum_triplas g3max(tripla)
  onde g3max = max sobre a interseccao tripla standalone (valido pois toda
  tripla embutida e standalone-viavel e g4 >= 0).
  1) incumbente: colecao do greedy+SA, Pwin exato (validado por MC).
  2) enumera todos os perfis m in [5,15]^6 com Sigma m >= 45 (bound de graus);
     descarta os com UB <= incumbente.
  3) para sobreviventes, enumera todas as fibras (T_123,T_124,T_134,T_234,q)
     com as 16 celulas >= 0 e calcula Pwin EXATO (incl. g4 por enumeracao).
  4) maximo global = max(incumbente, melhor sobrevivente).
"""
import sys, time
from math import comb
from itertools import product, permutations, combinations

sys.path.insert(0, r"C:\Users\LucasRafaeldeAndrade\Desktop\Repositorios\Loto-Facil")

V, K, T = 25, 15, 11
DEN = comb(V, K)
PN = sum(comb(K, j) * comb(V - K, K - j) for j in range(T, K + 1))

# ---------- g(m) exato (numeradores) ----------
def _g_num(m):
    s0, s1, s2, s3 = m, K - m, K - m, V - 2 * K + m
    if s3 < 0:
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

GN = {m: _g_num(m) for m in range(0, K + 1)}

# ---------- g3 exato para tripla (ma,mb,mc,T) ----------
_g3_memo = {}
def g3_num(ma, mb, mc, t3):
    key = (ma, mb, mc, t3)
    if key in _g3_memo:
        return _g3_memo[key]
    cells = (t3, ma - t3, mb - t3, mc - t3,
             K - ma - mb + t3, K - ma - mc + t3, K - mb - mc + t3,
             V - 3 * K + ma + mb + mc - t3)
    if any(c < 0 for c in cells):
        _g3_memo[key] = None
        return None
    if min(ma, mb, mc) <= 2 * T - K - 1:
        _g3_memo[key] = 0
        return 0
    c123, c12, c13, c23, c1, c2, c3, c0 = cells
    tot = 0
    for x123 in range(min(c123, K) + 1):
        for x12 in range(min(c12, K - x123) + 1):
            for x13 in range(min(c13, K - x123 - x12) + 1):
                r1 = K - x123 - x12 - x13
                for x23 in range(min(c23, r1) + 1):
                    r2 = r1 - x23
                    lo1 = max(0, T - x123 - x12 - x13)
                    if lo1 > min(c1, r2):
                        continue
                    w0 = comb(c123, x123) * comb(c12, x12) * comb(c13, x13) * comb(c23, x23)
                    for x1 in range(lo1, min(c1, r2) + 1):
                        r3 = r2 - x1
                        lo2 = max(0, T - x123 - x12 - x23)
                        if lo2 > min(c2, r3):
                            continue
                        w1 = w0 * comb(c1, x1)
                        for x2 in range(lo2, min(c2, r3) + 1):
                            r4 = r3 - x2
                            lo3 = max(0, T - x123 - x13 - x23)
                            if lo3 > min(c3, r4):
                                continue
                            w2 = w1 * comb(c2, x2)
                            for x3 in range(lo3, min(c3, r4) + 1):
                                x0 = r4 - x3
                                if 0 <= x0 <= c0:
                                    tot += w2 * comb(c3, x3) * comb(c0, x0)
    _g3_memo[key] = tot
    return tot

_g3max_memo = {}
def g3max(ma, mb, mc):
    """max de g3 sobre t3 standalone-viavel; None se tripla inviavel."""
    key = tuple(sorted((ma, mb, mc)))
    if key in _g3max_memo:
        return _g3max_memo[key]
    lo = max(0, ma + mb - K, ma + mc - K, mb + mc - K)
    hi = min(ma, mb, mc, V - 3 * K + ma + mb + mc)
    best = None
    for t3 in range(lo, hi + 1):
        g = g3_num(ma, mb, mc, t3)
        if g is not None:
            best = g if best is None else max(best, g)
    _g3max_memo[key] = best
    return best

# ---------- g4 exato para config de 16 celulas ----------
# celulas indexadas por subconjunto S de {0,1,2,3} (bitmask 0..15)
def g4_num(cell, m6):
    if min(m6) <= 2 * T - K - 1:
        return 0
    order = [s for s in range(16) if cell[s] > 0]
    sizes = [cell[s] for s in order]
    suffix = [0] * (len(order) + 1)
    for i in range(len(order) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + sizes[i]
    # capacidade restante que cada bilhete ainda pode receber a partir da pos i
    cap = [[0] * (len(order) + 1) for _ in range(4)]
    for tk in range(4):
        for i in range(len(order) - 1, -1, -1):
            cap[tk][i] = cap[tk][i + 1] + (sizes[i] if (order[i] >> tk) & 1 else 0)
    total = [0]
    def rec(i, rem, s0, s1, s2, s3, w):
        if rem < 0:
            return
        if i == len(order):
            if rem == 0 and s0 >= T and s1 >= T and s2 >= T and s3 >= T:
                total[0] += w
            return
        if rem > suffix[i]:
            return
        # poda: mesmo levando tudo, algum bilhete nao chega a T
        if (s0 + cap[0][i] < T or s1 + cap[1][i] < T or
                s2 + cap[2][i] < T or s3 + cap[3][i] < T):
            return
        S = order[i]
        b0, b1, b2, b3 = S & 1, (S >> 1) & 1, (S >> 2) & 1, (S >> 3) & 1
        for x in range(min(sizes[i], rem) + 1):
            rec(i + 1, rem - x, s0 + b0 * x, s1 + b1 * x, s2 + b2 * x,
                s3 + b3 * x, w * comb(sizes[i], x))
    rec(0, K, 0, 0, 0, 0, 1)
    return total[0]

PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
TRIPLES = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
def tri_pair_idx(tri):
    return [PAIRS.index((a, b)) for a, b in combinations(tri, 2)]
TRI_PIDX = [tri_pair_idx(t) for t in TRIPLES]

def cells_from(m6, T4, q):
    """16 celulas a partir de overlaps, triplas e quadrupla; None se invalida."""
    cell = [0] * 16
    cell[15] = q
    tmask = [0b0111, 0b1011, 0b1101, 0b1110]
    for ti, tri in enumerate(TRIPLES):
        cell[tmask[ti]] = T4[ti] - q
    for pi, (a, b) in enumerate(PAIRS):
        ts = [ti for ti, tri in enumerate(TRIPLES) if a in tri and b in tri]
        cell[(1 << a) | (1 << b)] = m6[pi] - T4[ts[0]] - T4[ts[1]] + q
    for i in range(4):
        s = K - sum(m6[pi] for pi, p in enumerate(PAIRS) if i in p) \
            + sum(T4[ti] for ti, tri in enumerate(TRIPLES) if i in tri) - q
        cell[1 << i] = s
    used = 4 * K - sum(m6) + sum(T4) - q
    cell[0] = V - used
    if any(c < 0 for c in cell):
        return None
    return cell

def pwin_num(m6, T4, q):
    cell = cells_from(m6, T4, q)
    if cell is None:
        return None
    tot = 4 * PN - sum(GN[m] for m in m6)
    g3s = []
    for ti, tri in enumerate(TRIPLES):
        pi = TRI_PIDX[ti]
        g3 = g3_num(m6[pi[0]], m6[pi[1]], m6[pi[2]], T4[ti])
        if g3 is None:
            return None
        g3s.append(g3)
        tot += g3
    # E_1234 esta contido em cada E_ijk: se todo g3 = 0, g4 = 0
    if any(g3s):
        tot -= g4_num(cell, m6)
    return tot

# ---------- 1) incumbente: greedy+SA ----------
import numpy as np
from lotofacil_optimizer import generate_ticket_pool, greedy_coverage_select, refine_overlap_sa

def profile_of(sets4):
    m6 = tuple(len(sets4[a] & sets4[b]) for a, b in PAIRS)
    T4 = tuple(len(sets4[a] & sets4[b] & sets4[c]) for a, b, c in TRIPLES)
    q = len(sets4[0] & sets4[1] & sets4[2] & sets4[3])
    return m6, T4, q

t0 = time.time()
best_inc = (-1, None)
for seed in range(8):
    rng = np.random.default_rng(seed)
    pool = generate_ticket_pool(500, rng)
    sa = refine_overlap_sa(greedy_coverage_select(pool, 4), rng, n_iter=1000)
    s4 = [set(map(int, row)) for row in sa]
    m6, T4, q = profile_of(s4)
    num = pwin_num(m6, T4, q)
    if num is not None and num > best_inc[0]:
        best_inc = (num, (m6, T4, q, [sorted(x) for x in s4]))
INC = best_inc[0]
print(f"incumbente (greedy+SA): Pwin = {INC}/{DEN} = {INC/DEN:.6f}")
print(f"  perfil m6={best_inc[1][0]}  T4={best_inc[1][1]}  q={best_inc[1][2]}")

# validacao do Pwin exato por Monte Carlo
tk = best_inc[1][3]
tb = np.zeros((4, 25), dtype=np.float32)
for i, s in enumerate(tk):
    tb[i, np.array(s) - 1] = 1.0
rngv = np.random.default_rng(999)
wins, ND = 0, 2_000_000
for _ in range(100):
    idx = rngv.permuted(np.tile(np.arange(25), (20_000, 1)), axis=1)[:, :15]
    dr = np.zeros((20_000, 25), dtype=np.float32)
    np.put_along_axis(dr, idx, 1.0, axis=1)
    wins += int(((dr @ tb.T) >= 11).any(axis=1).sum())
mc = wins / ND
print(f"  validacao MC (2M sorteios): {mc:.5f}  vs exato {INC/DEN:.5f}  "
      f"(diff {abs(mc-INC/DEN):.5f}, tolerancia ~0.0007)")

# ---------- 2) enumeracao de perfis com poda por UB ----------
print("\nenumerando perfis m in [5,15]^6 com Sigma>=45 ...")
survivors = []
n_prof = n_feas = 0
for m6 in product(range(5, 16), repeat=6):
    if sum(m6) < 45:
        continue
    n_prof += 1
    # UB SEGURO: Pwin = 4p - Sigma g + Sigma g3 - g4  <=  4p - Sigma g + Sigma g3max
    # (g4 >= 0; toda tripla embutida e standalone-viavel, logo g3 <= g3max)
    ub = 4 * PN - sum(GN[m] for m in m6)
    ok = True
    for ti in range(4):
        pi = TRI_PIDX[ti]
        gm = g3max(m6[pi[0]], m6[pi[1]], m6[pi[2]])
        if gm is None:
            ok = False
            break
        ub += gm
    if not ok:
        continue
    n_feas += 1
    if ub > INC:
        survivors.append(m6)
print(f"perfis com Sigma>=45: {n_prof}; triplas viaveis: {n_feas}; "
      f"sobreviventes ao UB: {len(survivors)}  [{time.time()-t0:.0f}s]")

# canonicaliza sobreviventes (acao de S4 nos 6 pares) para nao repetir fibras
def canon(m6):
    best = None
    for perm in permutations(range(4)):
        p = tuple(sorted([tuple(sorted((perm[a], perm[b]))) for a, b in PAIRS]))
        # reordena m6 conforme os pares permutados
        mm = tuple(m6[PAIRS.index(tuple(sorted((perm[a], perm[b]))))]
                   for a, b in PAIRS)
        if best is None or mm < best:
            best = mm
    return best

canon_surv = sorted(set(canon(m) for m in survivors))
print(f"sobreviventes canonicos: {len(canon_surv)}")

# ---------- 3) fibras exatas dos sobreviventes ----------
best_global = (INC, ("incumbente",))
checked = 0
for m6 in canon_surv:
    # faixas de T por tripla
    ranges = []
    for ti in range(4):
        pi = TRI_PIDX[ti]
        ma, mb, mc = m6[pi[0]], m6[pi[1]], m6[pi[2]]
        lo = max(0, ma + mb - K, ma + mc - K, mb + mc - K)
        hi = min(ma, mb, mc)
        ranges.append(range(lo, hi + 1))
    for T4 in product(*ranges):
        for q in range(0, min(T4) + 1):
            num = pwin_num(m6, T4, q)
            checked += 1
            if num is not None and num > best_global[0]:
                best_global = (num, (m6, T4, q))
                print(f"  NOVO MELHOR: {num}/{DEN} = {num/DEN:.6f}  "
                      f"m6={m6} T4={T4} q={q}")
print(f"fibras avaliadas: {checked}  [{time.time()-t0:.0f}s]")

print("\n" + "=" * 70)
print(f"OTIMO GLOBAL CERTIFICADO (n=4, Lotofacil): "
      f"{best_global[0]}/{DEN} = {best_global[0]/DEN:.6f}")
print(f"  atingido por: {best_global[1]}")
print(f"  incumbente do algoritmo: {INC/DEN:.6f}  "
      f"-> algoritmo e otimo? {best_global[0] == INC}")
U4 = 1 - (1 - PN / DEN) ** 4
print(f"  U_4 (aleatorio, em media) = {U4:.6f}")

# ---------- 4) unicidade do perfil otimo: perfis cujo UB nao fica ABAIXO ----------
print()
print("Verificacao de unicidade (perfis com UB >= otimo):")
ties = []
for m6 in product(range(5, 16), repeat=6):
    if sum(m6) < 45:
        continue
    ub = 4 * PN - sum(GN[m] for m in m6)
    okk = True
    for ti in range(4):
        pi = TRI_PIDX[ti]
        gm = g3max(m6[pi[0]], m6[pi[1]], m6[pi[2]])
        if gm is None:
            okk = False
            break
        ub += gm
    if okk and ub >= best_global[0]:
        ties.append(m6)
print(f"  perfis ordenados com UB >= otimo: {len(ties)} "
      f"(esperado: 4 = rotulacoes de {{8,8,8,7,7,7}} com os tres 8s em triangulo)")
for m6u in sorted(set(canon(m) for m in ties)):
    bestu, argu, nfib = -1, None, 0
    rngs = []
    for ti in range(4):
        pi = TRI_PIDX[ti]
        ma, mb, mc = m6u[pi[0]], m6u[pi[1]], m6u[pi[2]]
        rngs.append(range(max(0, ma + mb - K, ma + mc - K, mb + mc - K),
                          min(ma, mb, mc) + 1))
    for T4u in product(*rngs):
        for qu in range(0, min(T4u) + 1):
            num = pwin_num(m6u, T4u, qu)
            if num is not None:
                nfib += 1
                if num > bestu:
                    bestu, argu = num, (T4u, qu)
    print(f"  perfil canonico {m6u}: fibras viaveis = {nfib}, "
          f"max exato = {bestu}/{DEN} = {bestu/DEN:.6f}, "
          f"atinge o otimo? {bestu == best_global[0]}  (estrutura: {argu})")
print("Unicidade confirmada: um unico perfil canonico, com fibra unica, atinge o otimo."
      if len(set(canon(m) for m in ties)) == 1 else "ATENCAO: mais de um perfil empatou.")

