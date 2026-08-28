# Verification scripts

Numerical and exhaustive checks supporting the paper's results.

- **verify_paper.py** — Recomputes Table 3.5 g(m) exactly; numerically refutes the exponential bound of (old) Prop 3.10 at n=2, m=5; exhaustively checks two-ticket monotonicity g(m+1) >= g(m) for all v <= 18 (0 violations, 738 ties g(m\*) = g(m\*+1)); exact full enumeration of all 3-ticket Venn configurations for Lotofácil (optimum = profile (7,7,6), Pwin = 0.314669); finds strict counterexamples to the pairwise-monotonicity conjecture in small universes; checks the random baseline against U_n (E[Pwin] of i.i.d. uniform collections = U_n exactly).

- **counterexample.py** — Brute-force verification (all 330 draws) of the explicit counterexample at (v,k,t) = (11,7,4), n = 3: overlaps (5,5,5) with triple intersection 5 gives Pwin = 65/66, while (6,5,5) with triple intersection 4 gives 329/330 — increasing one pairwise overlap increased Pwin. Also Monte Carlo of a balanced n = 5 design for Lotofácil (each element in exactly 3 of 5 tickets, pairwise overlaps in {7,8}): Pwin ≈ 0.4976.

- **sup_reading.py** — Checks the reformulated conjecture: f(overlap profile) = max over realizations (triple intersection) of Pwin is coordinatewise non-increasing; 0 violations over all (v,k,t) with v <= 11 and for Lotofácil (25,15,11) n = 3.

- **proof_check.py** — Validates the swap-bijection proof identity g(m+1) − g(m) = P(|A1∩R| = t, |A2∩R| = t−1, x ∈ R, y ∉ R) exactly, for all 10 increments of Table 3.5 and 2303 (v,k,t,m) cases with v <= 16 — 0 failures.

## Added in revision 2 (monotonicity resolution)

- **lemma_check.py** — Validates the pattern-preserving swap lemma (`lem:pattern-swap`) exactly: the identity ΔPwin = −P(S1 = t, W = t−1, all others fail, x ∈ R, y ∉ R) on 266 random exact instances with n ∈ {3,4}, v in 7..11 — 0 failures.

- **sup_extend.py** — Extends the exhaustive verification of best-realisation profile monotonicity (n = 3, Theorem `thm:profile-monotone`) to v ∈ {12,13}, all (k,t) — 0 violations.

- **n4_check.py** — Exhaustive enumeration of ALL four-ticket collections in nine small families; finds 54 violations of best-realisation monotonicity for n = 4, e.g. (v,k,t) = (9,3,2): F(2,2,2,2,2,1) = 42/84 < F(2,2,2,2,2,2) = 43/84 (sunflower {1,2,x}). Establishes Example `ex:n4-counterexample`.

- **n4_verify.py** — Independent re-verification of the n = 4 counterexamples (different code path, prints argmax collections). Also used to compute the global optima of the two families: profiles (0,0,0,1,1,1) with 65/84 and (1,1,1,1,1,2) with 80/126 — both attaining the degree bound with the most balanced profile (Remark `rem:balance-principle`).

- **certify_n4.py** — Certified branch-and-bound for the global optimum with n = 4 Lotofácil tickets (Theorem `thm:certified-optima`). Uses the sound upper bound Pwin <= 4p − Σ g(m_ij) + Σ g3max over all 1,733,305 pairwise profiles with Σ m_ij >= 45; no profile's bound strictly exceeds the exact value of the greedy+SA collection, 1,322,189/3,268,760 ≈ 0.404493, attained by the balanced profile {8,8,8,7,7,7} (unique intersection structure, empty four-way intersection). Exact integer arithmetic throughout; the optimal collection is cross-validated by 2M-draw Monte Carlo. Runs in ~10 s.

## Added in revision 3 (certificates for n = 5 and n = 6)

- **certify_n5.jl** — Self-contained Julia certifier for n ∈ {4,5,6} (Theorem `thm:certified-optima`), sharing no code with the Python implementation. Bonferroni upper bound `n·p − Σg + Σg3max`, depth-first search over profiles pruned against the incumbent (parallel over the first three overlaps), full enumeration of admissible intersection structures constrained by degree moments and non-negative Möbius cells, exact inclusion–exclusion, and brute-force cross-validation over all C(25,15) = 3,268,760 draws. Self-tests reproduce the Python g and g3 tables; running `julia certify_n5.jl 4` reproduces the independently computed n = 4 certificate as a regression gate.

  Usage: `julia -t 10 certify_n5.jl [4|5|6|all|ties6]`. Results — n=4: 1,322,189/3,268,760 (2.6×10⁴ nodes, seconds); n=5: 1,626,630/3,268,760 (1.9×10⁷ nodes, 12 s); n=6: 1,840,731/3,268,760 (2.8×10¹¹ nodes, 13.5 h on ten cores). Mode `ties6` counts the optimal intersection structures of the n = 6 optimum (exactly 954). Progress log: `certify_n5_run.log`; surviving profiles: `certify_n{4,5,6}_survivors.csv`.

- **optima_decomposition.py** — Confirms the decomposition of Remark `rem:optimal-structure`: at all four certified optima, `Pwin·C(25,15) = n·p̂ − Σg + Σg3` exactly, with every fourth- and higher-order term vanishing (0, 160, 125 and 2,850 for n = 3,4,5,6). Also verifies that Σg3 = 2,850 is the maximum attainable for n = 6 subject to ΣT₃ = 70 over 20 triples, and that the degree sequences are forced ((3¹⁰,2¹⁵), (3²⁵), (4¹⁵,3¹⁰)).

- **sa_vs_certified.py** — Runs greedy+SA from ten independent seeds for n = 3,4,5,6 and evaluates each output exactly by enumerating all 3,268,760 draws. The certified optimum is attained in 10, 3, 9 and 3 of ten runs respectively — the algorithm reaches the global optimum in every certified case, but not from every start (Section 5).
