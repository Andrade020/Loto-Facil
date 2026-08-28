# -*- coding: utf-8 -*-
# certify_n5.jl -- Certificado exato do otimo global de P_win na Lotofacil
# (v=25, k=15, t=11) para n bilhetes: n=4 (gate de validacao contra o
# certificado Python ja auditado), n=5 (alvo da rodada) e n=6 (bonus).
#
# Metodo (aritmetica inteira exata, Int64; sem dependencias externas):
#   P_win * C(25,15) = sum_{U != vazio} (-1)^{|U|+1} J(U),
#   onde J(U) = # sorteios em que TODOS os bilhetes de U ganham (>= t acertos).
#   Bonferroni (truncar apos as triplas) da um limite superior valido:
#     P_win*DEN <= n*PN - sum_pares g(m_ij) + sum_triplas g3max(tripla).
#
#   Etapa 1 (incumbente): melhor rotulacao de multiset(s) balanceado(s), com
#     maximo exato sobre as fibras; validado por forca bruta (Gosper) sobre
#     todos os C(25,15) = 3.268.760 sorteios.
#   Etapa 2 (perfis): DFS sobre m em [5,15]^C(n,2) com Sigma m >= SMIN
#     (bound de graus, convexidade de C(d,2)) e poda pelo UB de Bonferroni,
#     reforcado por DP do minimo Sigma g restante.  Sobreviventes: UB >= INC.
#   Etapa 3 (fibras): para cada sobrevivente canonico, enumeracao completa
#     das interseccoes de ordem alta (T3 por tripla, T4 por quadrupla, ...)
#     com celulas de Moebius >= 0 e restricoes de momentos de grau; P_win
#     exato por inclusao-exclusao.  Otimo global = max(INC, sobreviventes).
#   Etapa 4 (unicidade): perfis/fibras que atingem o otimo.
#   Etapa 5 (validacao): colecao explicita do otimo conferida por Gosper.
#
# Uso:  julia certify_n5.jl [4|5|6|all]     (default: all = 4, depois 5, depois 6)

using Dates
using Printf

const V  = 25
const K  = 15
const TT = 11
const DEN = binomial(25, 15)          # 3_268_760
const PN  = sum(binomial(15, j) * binomial(10, 15 - j) for j in 11:15)  # 346_126

# tabela de binomiais (indices 1-based: BINT[n+1, k+1])
const BINT = [j <= i ? binomial(i, j) : 0 for i in 0:25, j in 0:25]
@inline bin(n::Int, k::Int) = (k < 0 || k > n || n < 0) ? 0 : BINT[n+1, k+1]

# ---------------------------------------------------------------------------
# log
# ---------------------------------------------------------------------------
const LOGIO = Ref{IOStream}()
const SAYLOCK = ReentrantLock()
function say(msg::String)
    lock(SAYLOCK) do
        line = "[$(Dates.format(now(), "yyyy-mm-dd HH:MM:SS"))] $msg"
        println(line)
        flush(stdout)
        if isassigned(LOGIO)
            println(LOGIO[], line)
            flush(LOGIO[])
        end
    end
end

# ---------------------------------------------------------------------------
# motor unico: J(U) por enumeracao sobre celulas com poda
#   cells: vetor de tamanhos por mascara local (indice mask+1)
#   conta sorteios (K-subconjuntos) em que TODOS os nt bilhetes tem >= TT acertos
# ---------------------------------------------------------------------------
function jwin(cells::Vector{Int}, nt::Int)::Int
    ord = [msk for msk in 0:(1 << nt)-1 if cells[msk+1] > 0]
    sort!(ord, by = msk -> -count_ones(msk))
    nc = length(ord)
    sizes = [cells[msk+1] for msk in ord]
    masks = ord
    suf = zeros(Int, nc + 1)
    cap = zeros(Int, nt, nc + 1)
    for i in nc:-1:1
        suf[i] = suf[i+1] + sizes[i]
        for t in 1:nt
            cap[t, i] = cap[t, i+1] + (((masks[i] >> (t-1)) & 1) == 1 ? sizes[i] : 0)
        end
    end
    scores = zeros(Int, nt)
    function rec(i::Int, rem::Int, w::Int)::Int
        if i > nc
            rem == 0 || return 0
            for t in 1:nt
                scores[t] < TT && return 0
            end
            return w
        end
        rem > suf[i] && return 0
        alldone = true
        for t in 1:nt
            if scores[t] < TT
                scores[t] + cap[t, i] < TT && return 0
                alldone = false
            end
        end
        # todos ja ganharam: o restante distribui livremente
        alldone && return w * bin(suf[i], rem)
        tot = 0
        S = masks[i]
        sz = sizes[i]
        xmax = min(sz, rem)
        for x in 0:xmax
            if x > 0
                for t in 1:nt
                    ((S >> (t-1)) & 1) == 1 && (scores[t] += 1)
                end
            end
            tot += rec(i + 1, rem - x, w * bin(sz, x))
        end
        for t in 1:nt
            ((S >> (t-1)) & 1) == 1 && (scores[t] -= xmax)
        end
        return tot
    end
    return rec(1, K, 1)
end

# ---------------------------------------------------------------------------
# g(m): vitoria conjunta de um par com overlap m
# ---------------------------------------------------------------------------
function g_pair_direct(m::Int)::Int
    s3 = V - 2K + m
    s3 < 0 && return 0
    m <= 2TT - K - 1 && return 0
    cells = zeros(Int, 4)
    cells[0b11 + 1] = m
    cells[0b01 + 1] = K - m
    cells[0b10 + 1] = K - m
    cells[0b00 + 1] = s3
    return jwin(cells, 2)
end
const GN = [g_pair_direct(m) for m in 0:15]   # GN[m+1]
@inline gpair(m::Int) = GN[m+1]

# ---------------------------------------------------------------------------
# g3(ma,mb,mc,t3): vitoria conjunta de tripla; -1 se celulas invalidas
#   ma=m12, mb=m13, mc=m23 (simetrico sob permutacao dos tres)
# ---------------------------------------------------------------------------
const G3MEMO = Dict{NTuple{4,Int},Int}()
function g3_num(ma::Int, mb::Int, mc::Int, t3::Int)::Int
    a, b, c = ma, mb, mc
    if a > b; a, b = b, a; end
    if b > c; b, c = c, b; end
    if a > b; a, b = b, a; end
    key = (a, b, c, t3)
    haskey(G3MEMO, key) && return G3MEMO[key]
    cl = (t3, a - t3, b - t3, c - t3,
          K - a - b + t3, K - a - c + t3, K - b - c + t3,
          V - 3K + a + b + c - t3)
    r = 0
    if any(x -> x < 0, cl)
        r = -1
    elseif a <= 2TT - K - 1
        r = 0
    else
        cells = zeros(Int, 8)
        cells[0b111 + 1] = cl[1]
        cells[0b011 + 1] = cl[2]
        cells[0b101 + 1] = cl[3]
        cells[0b110 + 1] = cl[4]
        cells[0b001 + 1] = cl[5]
        cells[0b010 + 1] = cl[6]
        cells[0b100 + 1] = cl[7]
        cells[0b000 + 1] = cl[8]
        r = jwin(cells, 3)
    end
    G3MEMO[key] = r
    return r
end

function t3_range(ma::Int, mb::Int, mc::Int)
    lo = max(0, ma + mb - K, ma + mc - K, mb + mc - K)
    hi = min(ma, mb, mc, ma + mb + mc - (3K - V))
    return lo, hi
end

const G3MAXMEMO = Dict{NTuple{3,Int},Int}()
function g3max_of(ma::Int, mb::Int, mc::Int)::Int   # -1 se tripla inviavel
    a, b, c = ma, mb, mc
    if a > b; a, b = b, a; end
    if b > c; b, c = c, b; end
    if a > b; a, b = b, a; end
    key = (a, b, c)
    haskey(G3MAXMEMO, key) && return G3MAXMEMO[key]
    lo, hi = t3_range(a, b, c)
    best = -1
    for t3 in lo:hi
        g = g3_num(a, b, c, t3)
        g >= 0 && (best = max(best, g))
    end
    G3MAXMEMO[key] = best
    return best
end

# tabelas de bound para triplas parcialmente fixadas (indices m-4 em 1:11)
const G3M2T = fill(-2, 11, 11)   # max sobre c de g3max(a,b,c); -1 = inviavel
const G3M1T = fill(-2, 11)
function build_g3_tables()
    for a in 5:15, b in 5:15
        best = -1
        for c in 5:15
            g = g3max_of(a, b, c)
            g >= 0 && (best = max(best, g))
        end
        G3M2T[a-4, b-4] = best
    end
    for a in 5:15
        best = -1
        for b in 5:15
            g = G3M2T[a-4, b-4]
            g >= 0 && (best = max(best, g))
        end
        G3M1T[a-4] = best
    end
end

# ---------------------------------------------------------------------------
# combinatoria basica propria (sem pacotes)
# ---------------------------------------------------------------------------
function all_perms(n::Int)
    out = Vector{Vector{Int}}()
    cur = collect(1:n)
    function rec(i)
        if i == n
            push!(out, copy(cur))
            return
        end
        for j in i:n
            cur[i], cur[j] = cur[j], cur[i]
            rec(i + 1)
            cur[i], cur[j] = cur[j], cur[i]
        end
    end
    rec(1)
    return out
end

function multiset_perms(vals::Vector{Int})
    out = Vector{Vector{Int}}()
    counts = Dict{Int,Int}()
    for v in vals
        counts[v] = get(counts, v, 0) + 1
    end
    ks = sort(collect(keys(counts)))
    cur = Int[]
    function rec()
        if length(cur) == length(vals)
            push!(out, copy(cur))
            return
        end
        for v in ks
            counts[v] == 0 && continue
            counts[v] -= 1
            push!(cur, v)
            rec()
            pop!(cur)
            counts[v] += 1
        end
    end
    rec()
    return out
end

# ---------------------------------------------------------------------------
# estrutura por n: pares, triplas, indices
# ---------------------------------------------------------------------------
struct Geometry
    n::Int
    np::Int
    por::Vector{Tuple{Int,Int}}          # ordem dos slots de pares
    pidx::Matrix{Int}                    # pidx[i,j] = slot do par {i,j}
    tsl::Vector{NTuple{3,Int}}           # slots dos 3 pares de cada tripla
    perms::Vector{Vector{Int}}
    smin::Int
end

function geometry(n::Int)
    por = Tuple{Int,Int}[]
    pidx = zeros(Int, n, n)
    for j in 2:n, i in 1:j-1
        push!(por, (i, j))
        pidx[i, j] = length(por)
        pidx[j, i] = length(por)
    end
    tsl = NTuple{3,Int}[]
    for a in 1:n, b in a+1:n, c in b+1:n
        push!(tsl, (pidx[a, b], pidx[a, c], pidx[b, c]))   # slots crescentes
    end
    q, r = divrem(n * K, V)
    smin = r * binomial(q + 1, 2) + (V - r) * binomial(q, 2)
    return Geometry(n, length(por), por, pidx, tsl, all_perms(n), smin)
end

function canon_profile(geo::Geometry, m::Vector{Int})
    best = ntuple(s -> 99, geo.np)
    for p in geo.perms
        t = ntuple(s -> m[geo.pidx[p[geo.por[s][1]], p[geo.por[s][2]]]], geo.np)
        t < best && (best = t)
    end
    return best
end

# ---------------------------------------------------------------------------
# momentos de grau: para perfil com soma S, quais (S3,S4,S5,S6) sao possiveis
#   Sl = sum_x C(d_x, l);  restricoes: sum d = nK, sum d^2 = 2S + nK
# ---------------------------------------------------------------------------
function moment_tuples(n::Int, S::Int)
    M1 = n * K
    M2 = 2 * S + n * K
    out = Set{NTuple{4,Int}}()
    nd = zeros(Int, n + 1)
    function rec(d::Int, remN::Int, rem1::Int, rem2::Int)
        if d == 0
            if rem1 == 0 && rem2 == 0
                nd[1] = remN
                s3 = sum(nd[dd+1] * bin(dd, 3) for dd in 0:n)
                s4 = sum(nd[dd+1] * bin(dd, 4) for dd in 0:n)
                s5 = sum(nd[dd+1] * bin(dd, 5) for dd in 0:n)
                s6 = sum(nd[dd+1] * bin(dd, 6) for dd in 0:n)
                push!(out, (s3, s4, s5, s6))
                nd[1] = 0
            end
            return
        end
        for c in 0:remN
            d * c > rem1 && break
            d * d * c > rem2 && break
            nd[d+1] = c
            rec(d - 1, remN - c, rem1 - d * c, rem2 - d * d * c)
            nd[d+1] = 0
        end
    end
    rec(n, V, M1, M2)
    return collect(out)
end

# ---------------------------------------------------------------------------
# celulas marginais de um subconjunto U de bilhetes (Moebius no reticulado
# de submascaras de U), em mascaras locais comprimidas
# ---------------------------------------------------------------------------
function marginal_cells(n::Int, I::Vector{Int}, U::Int)
    ell = count_ones(U)
    bits = [t for t in 0:n-1 if ((U >> t) & 1) == 1]
    cells = zeros(Int, 1 << ell)
    for lS in 0:(1 << ell)-1
        S = 0
        for (li, t) in enumerate(bits)
            ((lS >> (li-1)) & 1) == 1 && (S |= 1 << t)
        end
        rest = U & ~S
        c = 0
        sub = rest
        while true
            W = S | sub
            c += (iseven(count_ones(sub)) ? 1 : -1) * I[W+1]
            sub == 0 && break
            sub = (sub - 1) & rest
        end
        cells[lS+1] = c
    end
    return cells
end

# ---------------------------------------------------------------------------
# inclusao-exclusao exata dado I completo (I[mask+1] = |intersecao|)
# ---------------------------------------------------------------------------
const J4MEMO = Dict{NTuple{16,Int},Int}()
const J5MEMO = Dict{NTuple{32,Int},Int}()
const J6MEMO = Dict{NTuple{64,Int},Int}()

function joint_of(n::Int, I::Vector{Int}, U::Int)::Int
    pc = count_ones(U)
    if pc == 1
        return PN
    elseif pc == 2
        return gpair(I[U+1])
    end
    bits = [t for t in 0:n-1 if ((U >> t) & 1) == 1]
    # exclusividade mutua: par com overlap <= 2t-k-1 => J(U) = 0
    for i in 1:length(bits), j in i+1:length(bits)
        I[((1 << bits[i]) | (1 << bits[j])) + 1] <= 2TT - K - 1 && return 0
    end
    if pc == 3
        a, b, c = bits[1], bits[2], bits[3]
        m1 = I[((1 << a) | (1 << b)) + 1]
        m2 = I[((1 << a) | (1 << c)) + 1]
        m3 = I[((1 << b) | (1 << c)) + 1]
        g = g3_num(m1, m2, m3, I[U+1])
        @assert g >= 0 "g3 inviavel em fibra supostamente valida"
        return g
    end
    cells = marginal_cells(n, I, U)
    if pc == 4
        key = NTuple{16,Int}(cells)
        haskey(J4MEMO, key) && return J4MEMO[key]
        r = jwin(cells, 4)
        J4MEMO[key] = r
        return r
    elseif pc == 5
        key = NTuple{32,Int}(cells)
        haskey(J5MEMO, key) && return J5MEMO[key]
        r = jwin(cells, 5)
        J5MEMO[key] = r
        return r
    else
        key = NTuple{64,Int}(cells)
        haskey(J6MEMO, key) && return J6MEMO[key]
        r = jwin(cells, 6)
        J6MEMO[key] = r
        return r
    end
end

function exact_num(n::Int, I::Vector{Int})::Int
    tot = 0
    for U in 1:(1 << n)-1
        term = joint_of(n, I, U)
        tot += isodd(count_ones(U)) ? term : -term
    end
    return tot
end

# ---------------------------------------------------------------------------
# ETAPA B: maximo exato sobre as fibras de um perfil
#   retorna (best, ties, nfibras); ties = vetores I que atingem best (ate 500)
#   floor0: poda sonora -- descarta apenas fibras com bound < max(floor0, best)
# ---------------------------------------------------------------------------
function fiber_max(geo::Geometry, mvec::Vector{Int}, floor0::Int)
    n = geo.n
    NM = 1 << n
    I = fill(-1, NM)
    I[1] = V
    for t in 1:n
        I[(1 << (t-1)) + 1] = K
    end
    for (s, (i, j)) in enumerate(geo.por)
        I[((1 << (i-1)) | (1 << (j-1))) + 1] = mvec[s]
    end
    S = sum(mvec)
    base = n * PN - sum(gpair(mv) for mv in mvec)
    moments = moment_tuples(n, S)
    isempty(moments) && return (-1, Vector{Vector{Int}}(), 0)

    ulist = Int[]
    for ell in 3:n, U in 0:NM-1
        count_ones(U) == ell && push!(ulist, U)
    end
    nu = length(ulist)
    ntri = length(geo.tsl)
    lvl_first = Dict{Int,Int}()          # nivel => primeiro indice em ulist
    for (ui, U) in enumerate(ulist)
        ell = count_ones(U)
        haskey(lvl_first, ell) || (lvl_first[ell] = ui)
    end
    lvl_last = Dict{Int,Int}(ell => (ell == n ? nu : lvl_first[ell+1] - 1)
                             for ell in 3:n)

    function feasible_T(U::Int)
        hi = V
        for t in 1:n
            ((U >> (t-1)) & 1) == 1 && (hi = min(hi, I[(U & ~(1 << (t-1))) + 1]))
        end
        vals = Int[]
        for tv in 0:hi
            I[U+1] = tv
            all(x -> x >= 0, marginal_cells(n, I, U)) && push!(vals, tv)
        end
        I[U+1] = -1
        return vals
    end

    function g3_exact(U::Int)::Int
        bits = [t for t in 0:n-1 if ((U >> t) & 1) == 1]
        a, b, c = bits[1], bits[2], bits[3]
        m1 = I[((1 << a) | (1 << b)) + 1]
        m2 = I[((1 << a) | (1 << c)) + 1]
        m3 = I[((1 << b) | (1 << c)) + 1]
        return g3_num(m1, m2, m3, I[U+1])
    end

    best = Ref(-1)
    ties = Vector{Vector{Int}}()
    nfib = Ref(0)
    lvl_sum = zeros(Int, n)
    feas_cache = Dict{Int,Vector{Int}}()
    g3max_tri = Dict{Int,Int}()
    suf_lo = Dict{Int,Vector{Int}}()     # nivel => somas de sufixo dos minimos
    suf_hi = Dict{Int,Vector{Int}}()
    win_min = Dict{Int,Int}()            # nivel => menor/maior S_l permitido
    win_max = Dict{Int,Int}()

    function prefix_matches(mt::NTuple{4,Int}, upto::Int)::Bool
        for l in 3:upto
            (l <= 6 ? mt[l-2] : 0) == lvl_sum[l] || return false
        end
        return true
    end

    nties = Ref(0)
    function rec(ui::Int)
        if ui > nu
            any(mt -> prefix_matches(mt, n), moments) || return
            nfib[] += 1
            val = exact_num(n, I)
            if val > best[]
                best[] = val
                empty!(ties)
                nties[] = 0
            end
            if val == best[]
                nties[] += 1
                length(ties) < 500 && push!(ties, copy(I))
            end
            return
        end
        U = ulist[ui]
        ell = count_ones(U)
        if ui == lvl_first[ell]
            # nivel anterior fechou: prefixo de momentos precisa bater
            if ell > 3
                any(mt -> prefix_matches(mt, ell - 1), moments) || return
            end
            # recalcula viaveis do nivel e janelas de soma
            nlvl = lvl_last[ell] - lvl_first[ell] + 1
            lo = zeros(Int, nlvl + 1)
            hi = zeros(Int, nlvl + 1)
            for pos in nlvl:-1:1
                Uj = ulist[lvl_first[ell] + pos - 1]
                fv = feasible_T(Uj)
                isempty(fv) && return
                feas_cache[Uj] = fv
                lo[pos] = lo[pos+1] + minimum(fv)
                hi[pos] = hi[pos+1] + maximum(fv)
                if ell == 3
                    g3max_tri[Uj] = maximum(g3_num(
                        I[((1 << (t3b(Uj)[1])) | (1 << (t3b(Uj)[2]))) + 1],
                        I[((1 << (t3b(Uj)[1])) | (1 << (t3b(Uj)[3]))) + 1],
                        I[((1 << (t3b(Uj)[2])) | (1 << (t3b(Uj)[3]))) + 1],
                        tv) for tv in fv)
                end
            end
            suf_lo[ell] = lo
            suf_hi[ell] = hi
            wvals = Int[]
            for mt in moments
                prefix_matches(mt, ell - 1) && push!(wvals, ell <= 6 ? mt[ell-2] : 0)
            end
            isempty(wvals) && return
            win_min[ell] = minimum(wvals)
            win_max[ell] = maximum(wvals)
        end
        pos = ui - lvl_first[ell] + 1
        slo = suf_lo[ell]
        shi = suf_hi[ell]
        for tv in feas_cache[U]
            newsum = lvl_sum[ell] + tv
            newsum + slo[pos+1] > win_max[ell] && break     # tv crescente
            newsum + shi[pos+1] < win_min[ell] && continue
            I[U+1] = tv
            lvl_sum[ell] = newsum
            ok = true
            if ell == 3
                ub = base
                for uj in 1:ntri
                    Uj = ulist[uj]
                    ub += I[Uj+1] >= 0 ? g3_exact(Uj) : g3max_tri[Uj]
                end
                ub < max(floor0, best[]) && (ok = false)
            end
            ok && rec(ui + 1)
            lvl_sum[ell] = newsum - tv
            I[U+1] = -1
        end
    end

    # bits de uma tripla (auxiliar para g3max_tri)
    t3b_memo = Dict{Int,NTuple{3,Int}}()
    function t3b(U::Int)
        haskey(t3b_memo, U) && return t3b_memo[U]
        bits = [t for t in 0:n-1 if ((U >> t) & 1) == 1]
        r = (bits[1], bits[2], bits[3])
        t3b_memo[U] = r
        return r
    end

    rec(1)
    return (best[], ties, nfib[], nties[])
end

# ---------------------------------------------------------------------------
# ETAPA A: DFS sobre perfis com poda por UB de Bonferroni
# ---------------------------------------------------------------------------
function stage_a(geo::Geometry, INC::Int)
    n, np, ntri = geo.n, geo.np, length(geo.tsl)
    SMIN = geo.smin
    INF = typemax(Int) ÷ 4
    RMAX = np
    SMAX = 15 * np
    mingrem = fill(INF, RMAX + 1, SMAX + 2)
    for s in 0:SMAX+1
        mingrem[1, s+1] = s == 0 ? 0 : INF
    end
    for r in 1:RMAX, s in 0:SMAX+1
        bestv = INF
        for mv in 5:15
            rest = max(0, s - mv)
            prev = mingrem[r, rest+1]
            prev < INF && (bestv = min(bestv, gpair(mv) + prev))
        end
        mingrem[r+1, s+1] = bestv
    end

    NEGINF = typemin(Int) ÷ 2
    # paraleliza sobre prefixos (m1,m2,m3); tabelas de bound sao so-leitura
    # (G3MAXMEMO foi totalmente preenchida por build_g3_tables)
    prefixes = Tuple{Int,Int,Int}[]
    for m1 in 5:15, m2 in 5:15, m3 in 5:15
        push!(prefixes, (m1, m2, m3))
    end
    nT = length(prefixes)
    results = Vector{Tuple{Dict{Tuple{Vararg{Int}},Int},Int,Int}}(undef, nT)
    done_ct = Threads.Atomic{Int}(0)
    Threads.@threads :dynamic for pi in 1:nT
        m1, m2, m3 = prefixes[pi]
        m = zeros(Int, np)
        m[1], m[2], m[3] = m1, m2, m3
        surv = Dict{Tuple{Vararg{Int}},Int}()
        nlab = Ref(0)
        nodes = Ref(0)

        function ub_at(d::Int, sfix::Int, gfix::Int)::Int
            r = np - d
            need = max(0, SMIN - sfix)
            need > 15 * r && return NEGINF
            ub = n * PN - gfix - mingrem[r+1, need+1]
            for t in 1:ntri
                s1, s2, s3 = geo.tsl[t]
                local gm::Int
                if s3 <= d
                    gm = g3max_of(m[s1], m[s2], m[s3])
                elseif s2 <= d
                    gm = G3M2T[m[s1]-4, m[s2]-4]
                elseif s1 <= d
                    gm = G3M1T[m[s1]-4]
                else
                    gm = PN
                end
                gm < 0 && return NEGINF
                ub += gm
            end
            return ub
        end

        function dfs(d::Int, sfix::Int, gfix::Int)
            for mv in 5:15
                m[d+1] = mv
                nodes[] += 1
                if nodes[] % 1_000_000_000 == 0
                    say("  etapa A: worker $(prefixes[pi]): $(nodes[]) nos")
                end
                ub = ub_at(d + 1, sfix + mv, gfix + gpair(mv))
                ub < INC && continue
                if d + 1 == np
                    nlab[] += 1
                    cp = canon_profile(geo, m)
                    old = get(surv, cp, NEGINF)
                    ub > old && (surv[cp] = ub)
                else
                    dfs(d + 1, sfix + mv, gfix + gpair(mv))
                end
            end
        end

        # espelha as podas dos 3 primeiros niveis da DFS sequencial
        s1v = m1; g1v = gpair(m1)
        s2v = s1v + m2; g2v = g1v + gpair(m2)
        s3v = s2v + m3; g3v = g2v + gpair(m3)
        nodes[] += 3
        ok = ub_at(1, s1v, g1v) >= INC && ub_at(2, s2v, g2v) >= INC &&
             ub_at(3, s3v, g3v) >= INC
        ok && dfs(3, s3v, g3v)
        results[pi] = (surv, nlab[], nodes[])
        c = Threads.atomic_add!(done_ct, 1) + 1
        (c % 250 == 0 || c == nT) && say("  etapa A: $c/$nT prefixos concluidos")
    end
    survivors = Dict{Tuple{Vararg{Int}},Int}()
    nlab_tot = 0
    nodes_tot = 0
    for pi in 1:nT
        surv, nl, nd = results[pi]
        nlab_tot += nl
        nodes_tot += nd
        for (cp, ub) in surv
            old = get(survivors, cp, NEGINF)
            ub > old && (survivors[cp] = ub)
        end
    end
    return survivors, nlab_tot, nodes_tot
end

# ---------------------------------------------------------------------------
# validacao por forca bruta: Gosper sobre todos os C(25,15) sorteios
# ---------------------------------------------------------------------------
function brute_force_pwin(n::Int, I::Vector{Int})::Int
    NM = 1 << n
    cells = zeros(Int, NM)
    for Smask in 0:NM-1
        rest = (NM - 1) & ~Smask
        c = 0
        sub = rest
        while true
            W = Smask | sub
            c += (iseven(count_ones(sub)) ? 1 : -1) * I[W+1]
            sub == 0 && break
            sub = (sub - 1) & rest
        end
        @assert c >= 0 "celula negativa na validacao"
        cells[Smask+1] = c
    end
    @assert sum(cells) == V
    ticks = zeros(UInt32, n)
    e = 0
    for Smask in 0:NM-1, _ in 1:cells[Smask+1]
        for t in 1:n
            ((Smask >> (t-1)) & 1) == 1 && (ticks[t] |= UInt32(1) << e)
        end
        e += 1
    end
    @assert e == V
    for t in 1:n
        @assert count_ones(ticks[t]) == K
    end
    wins = 0
    draw = (UInt32(1) << K) - UInt32(1)
    lim = UInt32(1) << V
    while draw < lim
        for t in 1:n
            if count_ones(draw & ticks[t]) >= TT
                wins += 1
                break
            end
        end
        u = draw & (~draw + UInt32(1))
        vv = draw + u
        draw = vv | (((draw ⊻ vv) ÷ u) >> 2)
    end
    return wins
end

# ---------------------------------------------------------------------------
# certificacao completa para um n
# ---------------------------------------------------------------------------
function certify(n::Int, inc_multisets::Vector{Vector{Int}};
                 expected_opt::Union{Int,Nothing} = nothing)
    geo = geometry(n)
    say(repeat("=", 74))
    say("CERTIFICACAO n=$n  (V=$V, K=$K, T=$TT)  SMIN=$(geo.smin)  pares=$(geo.np)")
    t0 = time()

    # ---- etapa 1: incumbente ----
    say("etapa 1: incumbente (rotulacoes de $(length(inc_multisets)) multiset(s))")
    INC = -1
    inc_I = Int[]
    inc_prof = Int[]
    nlab_total = 0
    for ms in inc_multisets
        @assert length(ms) == geo.np
        for lab in multiset_perms(ms)
            nlab_total += 1
            bestv, tiesv, _ = fiber_max(geo, lab, INC)
            if bestv > INC
                INC = bestv
                inc_I = copy(tiesv[1])
                inc_prof = copy(lab)
            end
        end
    end
    say("  incumbente: $INC/$DEN = $(@sprintf("%.6f", INC / DEN))  " *
        "($nlab_total rotulacoes; perfil $(Tuple(inc_prof)))")
    @assert INC > 0 "incumbente invalido"

    bf = brute_force_pwin(n, inc_I)
    say("  validacao Gosper do incumbente: forca bruta = $bf  " *
        (bf == INC ? "[OK, igual ao exato]" : "[FALHOU!]"))
    @assert bf == INC "incl-excl != forca bruta no incumbente"

    # ---- etapa 2: perfis ----
    say("etapa 2: DFS sobre perfis (poda Bonferroni, INC=$INC)")
    survivors, nlab, nodes = stage_a(geo, INC)
    say("  nos visitados: $nodes; perfis rotulados sobreviventes: $nlab; " *
        "canonicos: $(length(survivors))  [$(round(time() - t0, digits = 1))s]")
    inc_canon = canon_profile(geo, inc_prof)
    @assert haskey(survivors, inc_canon) "perfil do incumbente nao sobreviveu (BUG!)"

    spath = joinpath(@__DIR__, "certify_n$(n)_survivors.csv")
    open(spath, "w") do io
        for (cp, ub) in sort(collect(survivors), by = x -> -x[2])
            println(io, join(cp, ","), ",", ub)
        end
    end
    say("  sobreviventes gravados em $spath")

    # ---- etapa 3: fibras exatas ----
    say("etapa 3: maximo exato sobre as fibras de cada sobrevivente")
    OPT = INC
    results = Vector{Tuple{Tuple{Vararg{Int}},Int,Int}}()
    ndone = 0
    for (cp, ub) in sort(collect(survivors), by = x -> -x[2])
        bestv, _, nf = fiber_max(geo, collect(cp), OPT)
        push!(results, (cp, bestv, nf))
        bestv > OPT && say("  NOVO MELHOR: $bestv/$DEN em perfil $cp")
        OPT = max(OPT, bestv)
        ndone += 1
        ndone % 200 == 0 && say("  ... $ndone/$(length(survivors)) perfis processados")
    end
    say("  otimo global: $OPT/$DEN = $(@sprintf("%.6f", OPT / DEN))  " *
        "[$(round(time() - t0, digits = 1))s]")

    # ---- etapa 4: unicidade ----
    say("etapa 4: unicidade (perfis cujo maximo exato atinge o otimo)")
    winners = [(cp, nf) for (cp, bestv, nf) in results if bestv == OPT]
    for (cp, _) in winners
        bestv, tiesv, nf, ntv = fiber_max(geo, collect(cp), OPT - 1)
        @assert bestv == OPT
        say("  perfil $cp: fibras viaveis (bound >= OPT-1): $nf; " *
            "fibras que atingem o otimo (contagem exata): $ntv")
        for tI in tiesv[1:min(end, 6)]
            lv3 = [tI[U+1] for U in 0:(1 << n)-1 if count_ones(U) == 3]
            lv4 = [tI[U+1] for U in 0:(1 << n)-1 if count_ones(U) == 4]
            lvh = [tI[U+1] for U in 0:(1 << n)-1 if count_ones(U) > 4]
            say("    fibra otima: T3=$(Tuple(lv3)) T4=$(Tuple(lv4)) T5+=$(Tuple(lvh))")
        end
    end
    say("  perfis canonicos que atingem o otimo: $(length(winners))")

    # ---- etapa 5: validacao final ----
    bestv, tiesv, _ = fiber_max(geo, collect(winners[1][1]), OPT - 1)
    @assert bestv == OPT
    bf2 = brute_force_pwin(n, tiesv[1])
    say("etapa 5: validacao Gosper do otimo: forca bruta = $bf2  " *
        (bf2 == OPT ? "[OK, igual ao exato]" : "[FALHOU!]"))
    @assert bf2 == OPT "incl-excl != forca bruta no otimo"

    if expected_opt !== nothing
        ok = OPT == expected_opt
        say("GATE: esperado $expected_opt, obtido $OPT  " * (ok ? "[OK]" : "[FALHOU!]"))
        @assert ok "gate n=$n falhou"
    end
    Un = 1 - (1 - PN / DEN)^n
    say("RESULTADO n=$n: OTIMO CERTIFICADO = $OPT/$DEN = " *
        "$(@sprintf("%.6f", OPT / DEN))   (U_$n aleatorio = " *
        "$(@sprintf("%.6f", Un));  incumbente ja era otimo? $(OPT == INC))")
    say("tempo total n=$n: $(round(time() - t0, digits = 1))s")
    return OPT
end

# ---------------------------------------------------------------------------
# auto-testes (valores certificados independentemente em Python, 18-19/jul/2026)
# ---------------------------------------------------------------------------
function selftest()
    say("auto-testes das tabelas exatas ...")
    @assert DEN == 3_268_760
    @assert PN == 346_126
    @assert gpair(5) == 0 && gpair(6) == 0
    @assert gpair(7) == 4_900
    @assert gpair(8) == 15_925
    @assert gpair(9) == 32_500
    @assert gpair(10) == 54_500
    @assert gpair(15) == PN
    @assert g3max_of(7, 7, 7) == 0
    @assert g3max_of(7, 7, 8) == 0
    @assert g3max_of(7, 8, 8) == 25
    @assert g3max_of(8, 8, 8) == 160
    @assert g3max_of(7, 8, 9) == 115
    @assert g3max_of(8, 9, 9) == 1_216
    @assert g3max_of(9, 9, 9) == 3_375
    @assert g3_num(8, 8, 8, 4) == 160
    say("auto-testes: OK (g e g3 conferem com o certificado Python)")
end

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
function main()
    mode = length(ARGS) >= 1 ? ARGS[1] : "all"
    LOGIO[] = open(joinpath(@__DIR__, "certify_n5_run.log"), "a")
    say(repeat("#", 74))
    say("certify_n5.jl -- inicio (modo=$mode, Julia $(VERSION))")
    build_g3_tables()
    selftest()
    if mode in ("4", "all")
        certify(4, [[7, 7, 7, 8, 8, 8]]; expected_opt = 1_322_189)
    end
    if mode in ("5", "all")
        certify(5, [vcat(fill(7, 5), fill(8, 5))])
    end
    if mode in ("6", "all")
        say("n=6 e BONUS: pode nao terminar ate de manha; progresso fica no log")
        certify(6, [fill(8, 15), vcat([7], fill(8, 13), [9])])
    end
    if mode == "ties6"
        # contagem exata das fibras otimas do perfil {8^15} (n=6), sem re-certificar
        geo = geometry(6)
        bestv, tiesv, nf, ntv = fiber_max(geo, fill(8, 15), 1_840_731 - 1)
        say("ties6: perfil {8^15}: max = $bestv/$DEN; fibras viaveis = $nf; " *
            "fibras que atingem o otimo (contagem exata) = $ntv")
        @assert bestv == 1_840_731
    end
    say("certify_n5.jl -- fim")
    close(LOGIO[])
end

main()
