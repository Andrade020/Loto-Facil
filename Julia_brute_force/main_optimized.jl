using JuMP
using HiGHS
using Gurobi  # comment out if unavailable; switch to HiGHS below

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

"""
    overlap_matrix(x) -> Matrix{Int}

Pairwise overlap |Aᵢ ∩ Aⱼ| for all (i,j), computed via matrix multiplication
instead of nested loops. Diagonal = k (self-overlap, not used in objectives).
"""
function overlap_matrix(x::AbstractMatrix{<:Real})
    return round.(Int, x * x')
end

"""
    total_overlap(x) -> Int

Sum of |Aᵢ ∩ Aⱼ| over all pairs i < j.  This is the objective Ω(A) of the
total-overlap model.
"""
function total_overlap(x::AbstractMatrix{<:Real})
    ov = overlap_matrix(x)
    n  = size(x, 1)
    return sum(ov[i, j] for i in 1:n for j in i+1:n)
end

"""
    max_pairwise_overlap(x) -> Int

Maximum |Aᵢ ∩ Aⱼ| over all pairs i < j.  This is the objective M of the
minimax model.
"""
function max_pairwise_overlap(x::AbstractMatrix{<:Real})
    ov = overlap_matrix(x)
    n  = size(x, 1)
    return maximum(ov[i, j] for i in 1:n for j in i+1:n)
end

"""
    print_overlap(overlap, label)

Print the upper-triangular part of an overlap matrix with a header label.
"""
function print_overlap(overlap::AbstractMatrix{<:Integer}, label::String)
    n = size(overlap, 1)
    println("\n", label)
    for i in 1:n
        row = [j < i ? "." : j == i ? "-" : string(overlap[i, j]) for j in 1:n]
        println(join(row, "\t"))
    end
end

# ---------------------------------------------------------------------------
# Shared IP model construction
# ---------------------------------------------------------------------------

"""
    build_base_model(n, v, k, optimizer) -> JuMP.Model

Constructs the common MIP structure shared by both objectives:
  - Binary variables x[i,d]: ticket i contains number d
  - Continuous z[i,j,d] ∈ [0,1]: linearisation of x[i,d]·x[j,d]
  - Cardinality constraints: each ticket has exactly k numbers
  - McCormick linearisation of the product
  - Symmetry-breaking: fix first ticket and sort columns by frequency
  - Valid lower bound: every pair must overlap by at least m* = max(0, 2k-v)
"""
function build_base_model(n::Int, v::Int, k::Int, optimizer)
    @assert 1 <= k <= v "Need 1 ≤ k ≤ v"
    @assert n >= 2       "Need at least 2 tickets"

    model = Model(optimizer)

    @variable(model, x[1:n, 1:v], Bin)
    @variable(model, 0 <= z[i=1:n, j=i+1:n, d=1:v] <= 1)

    # Each ticket has exactly k numbers
    @constraint(model, [i = 1:n], sum(x[i, d] for d in 1:v) == k)

    # McCormick linearisation of z[i,j,d] = x[i,d] * x[j,d]
    @constraint(model, [i = 1:n, j = i+1:n, d = 1:v], z[i, j, d] <= x[i, d])
    @constraint(model, [i = 1:n, j = i+1:n, d = 1:v], z[i, j, d] <= x[j, d])
    @constraint(model, [i = 1:n, j = i+1:n, d = 1:v], z[i, j, d] >= x[i, d] + x[j, d] - 1)

    # Symmetry breaking 1: fix first ticket to {1, ..., k}
    for d in 1:k     @constraint(model, x[1, d] == 1) end
    for d in k+1:v   @constraint(model, x[1, d] == 0) end

    # Symmetry breaking 2: columns ordered by decreasing frequency
    @constraint(model, [d = 1:v-1],
        sum(x[i, d] for i in 1:n) >= sum(x[i, d+1] for i in 1:n))

    # Valid inequality: pigeonhole lower bound on pairwise overlap
    m_star = max(0, 2k - v)
    if m_star > 0
        @constraint(model, [i = 1:n, j = i+1:n],
            sum(z[i, j, d] for d in 1:v) >= m_star)
    end

    return model
end

# ---------------------------------------------------------------------------
# Model 1: minimise maximum pairwise overlap  (minimax)
# ---------------------------------------------------------------------------

"""
    solve_minimax(n, v, k; optimizer, silent) -> (model, x_sol or nothing)

Minimises M = max_{i<j} |Aᵢ ∩ Aⱼ|.
"""
function solve_minimax(n::Int, v::Int, k::Int;
                       optimizer = Gurobi.Optimizer,
                       silent::Bool = false)
    model = build_base_model(n, v, k, optimizer)
    silent && set_silent(model)

    z = model[:z]
    @variable(model, M >= 0)
    @constraint(model, [i = 1:n, j = i+1:n],
        sum(z[i, j, d] for d in 1:v) <= M)
    @objective(model, Min, M)

    optimize!(model)

    status = termination_status(model)
    println("[minimax] n=$n  status=$status")

    if has_values(model)
        x_sol = round.(Int, value.(model[:x]))
        M_val = round(Int, objective_value(model))
        println("[minimax] M = $M_val")
        return model, x_sol
    end
    return model, nothing
end

# ---------------------------------------------------------------------------
# Model 2: minimise total pairwise overlap  (sum)
# ---------------------------------------------------------------------------

"""
    solve_total(n, v, k; optimizer, silent) -> (model, x_sol or nothing)

Minimises Ω(A) = Σ_{i<j} |Aᵢ ∩ Aⱼ|.  This is the objective used in the
Simulated Annealing of the companion paper; here we solve it to optimality.
"""
function solve_total(n::Int, v::Int, k::Int;
                     optimizer = Gurobi.Optimizer,
                     silent::Bool = false)
    model = build_base_model(n, v, k, optimizer)
    silent && set_silent(model)

    z = model[:z]
    @objective(model, Min,
        sum(z[i, j, d] for i in 1:n for j in i+1:n for d in 1:v))

    optimize!(model)

    status = termination_status(model)
    println("[total]   n=$n  status=$status")

    if has_values(model)
        x_sol = round.(Int, value.(model[:x]))
        Ω = total_overlap(x_sol)
        println("[total]   Ω = $Ω")
        return model, x_sol
    end
    return model, nothing
end

# ---------------------------------------------------------------------------
# Comparison: minimax vs total-overlap solutions
# ---------------------------------------------------------------------------

"""
    compare_objectives(n, v, k; optimizer)

Solves both models and prints a side-by-side comparison.
"""
function compare_objectives(n::Int, v::Int, k::Int;
                             optimizer = Gurobi.Optimizer)
    println("\n=== Comparison: minimax vs total overlap (n=$n, v=$v, k=$k) ===")

    _, x1 = solve_minimax(n, v, k; optimizer = optimizer, silent = true)
    _, x2 = solve_total(  n, v, k; optimizer = optimizer, silent = true)

    if isnothing(x1) || isnothing(x2)
        println("No primal solution in at least one model.")
        return
    end

    ov1 = overlap_matrix(x1)
    ov2 = overlap_matrix(x2)

    println("\nMinimax  →  max_overlap=$(max_pairwise_overlap(x1)),  total_Ω=$(total_overlap(x1))")
    println("Total    →  max_overlap=$(max_pairwise_overlap(x2)),  total_Ω=$(total_overlap(x2))")

    print_overlap(ov1, "Overlap matrix (minimax):")
    print_overlap(ov2, "Overlap matrix (total):")

    diff_rows = [i for i in 1:n if any(x1[i, d] != x2[i, d] for d in 1:v)]
    if isempty(diff_rows)
        println("\nSolutions are identical.")
    else
        println("\nRows that differ: $(join(diff_rows, ", "))")
    end
end

# ---------------------------------------------------------------------------
# Benchmark across different values of n
# ---------------------------------------------------------------------------

"""
    run_benchmark(N_values, v, k; optimizer, silent)

Solves the total-overlap model for each n in N_values and reports runtime,
total overlap Ω, and maximum pairwise overlap M.
"""
function run_benchmark(N_values::Vector{Int}, v::Int, k::Int;
                       optimizer = Gurobi.Optimizer,
                       silent::Bool = true)
    println("\n=== Benchmark (v=$v, k=$k) ===")
    println("n\ttime(s)\tΩ\tM")

    for n in N_values
        t0 = time()
        _, x_sol = solve_total(n, v, k; optimizer = optimizer, silent = silent)
        elapsed = round(time() - t0, digits = 2)

        if !isnothing(x_sol)
            Ω = total_overlap(x_sol)
            M = max_pairwise_overlap(x_sol)
            println("$n\t$elapsed\t$Ω\t$M")
        else
            println("$n\tFAILED\t-\t-")
        end
    end
end

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

const V = 25
const K = 15

# Single run
run_benchmark([5, 10, 15, 20], V, K)

# Uncomment to compare the two objectives for n=5:
# compare_objectives(5, V, K)
