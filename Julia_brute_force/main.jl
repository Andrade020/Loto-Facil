using JuMP
using HiGHS
using Gurobi # Comment out if you don't have Gurobi installed

function overlap_objective(x::AbstractMatrix{<:Real})
    n, v = size(x)
    total = 0
    for i in 1:n
        for j in i+1:n
            total += round(Int, sum(x[i, d] * x[j, d] for d in 1:v))
        end
    end
    return total
end

function overlap_matrix(x::AbstractMatrix{<:Real})
    n, v = size(x)
    m = zeros(Int, n, n)
    for i in 1:n
        for j in 1:n
            m[i, j] = round(Int, sum(x[i, d] * x[j, d] for d in 1:v))
        end
    end
    return m
end

function print_upper_triangular_overlap(overlap::AbstractMatrix{<:Integer}, label::String)
    n = size(overlap, 1)
    println("\n", label)
    for i in 1:n
        row = String[]
        for j in 1:n
            if j < i
                push!(row, " ")
            elseif j == i
                push!(row, "-")
            else
                push!(row, string(overlap[i, j]))
            end
        end
        println(join(row, " "))
    end
end



function solve_model_max_overlap(n::Int, v::Int, k::Int)
    @assert 0 <= k <= v "Must have 0 <= k <= v."

    model = Model(Gurobi.Optimizer)
    # model = Model(HiGHS.Optimizer)

    @variable(model, x[1:n, 1:v], Bin)
    @variable(model, 0 <= z[i=1:n, j=i+1:n, d=1:v] <= 1)
    @variable(model, M >= 0)

    @constraint(model, [i = 1:n], sum(x[i, d] for d in 1:v) == k)

    @constraint(model, [i = 1:n, j = i+1:n, d = 1:v], z[i, j, d] <= x[i, d])
    @constraint(model, [i = 1:n, j = i+1:n, d = 1:v], z[i, j, d] <= x[j, d])
    @constraint(model, [i = 1:n, j = i+1:n, d = 1:v], z[i, j, d] >= x[i, d] + x[j, d] - 1)

    @constraint(model, [i = 1:n, j = i+1:n],
        sum(z[i, j, d] for d in 1:v) <= M
    )

    # 1. Fixar a primeira linha
    @constraint(model, [d = 1:k], x[1, d] == 1)
    @constraint(model, [d = k+1:v], x[1, d] == 0)

    # 2. Ordenar as cargas das colunas
    @constraint(model, [d = 1:v-1],
        sum(x[i, d] for i in 1:n) >= sum(x[i, d+1] for i in 1:n)
    )

    @objective(model, Min, M)

    # set silent
    # set_silent(model)
    optimize!(model)

    status = termination_status(model)
    primal_status_ = primal_status(model)

    println("[solve_model] Termination status: ", status)
    println("[solve_model] Primal status: ", primal_status_)

    if has_values(model)
        println("[solve_model] Objective value (M): ", objective_value(model))
        println("[solve_model] M = ", value(M))

        x_sol = value.(x)
        overlap = zeros(Int, n, n)
        for i in 1:n
            for j in 1:n
                overlap[i, j] = round(Int, sum(x_sol[i, d] * x_sol[j, d] for d in 1:v))
            end
        end

        print_upper_triangular_overlap(overlap, "Upper-triangular overlap matrix (solve_model):")
    end

    return model
end


function solve_model_total_overlap(n::Int, v::Int, k::Int)
    @assert 0 <= k <= v "Must have 0 <= k <= v."

    model = Model(Gurobi.Optimizer)
    # model = Model(HiGHS.Optimizer)

    @variable(model, x[1:n, 1:v], Bin)
    @variable(model, 0 <= z[i=1:n, j=i+1:n, d=1:v] <= 1)

    @constraint(model, [i = 1:n], sum(x[i, d] for d in 1:v) == k)

    @constraint(model, [i = 1:n, j = i+1:n, d = 1:v], z[i, j, d] <= x[i, d])
    @constraint(model, [i = 1:n, j = i+1:n, d = 1:v], z[i, j, d] <= x[j, d])
    @constraint(model, [i = 1:n, j = i+1:n, d = 1:v], z[i, j, d] >= x[i, d] + x[j, d] - 1)

    @objective(model, Min,
        sum(z[i, j, d] for i in 1:n for j in i+1:n for d in 1:v)
    )
    # set silent
    # set_silent(model)

    @constraint(model, [d = 1:k], x[1, d] == 1)
    @constraint(model, [d = k+1:v], x[1, d] == 0)


    @constraint(model, [d = 1:v-1],
        sum(x[i, d] for i in 1:n) >= sum(x[i, d+1] for i in 1:n)
    )


    optimize!(model)

    status = termination_status(model)
    primal_status_ = primal_status(model)

    println("[solve_model2] Termination status: ", status)
    println("[solve_model2] Primal status: ", primal_status_)

    if has_values(model)
        println("[solve_model2] Objective value: ", objective_value(model))
    end

    return model
end

function compare_solutions(n::Int, v::Int, k::Int)
    println("\n=== Comparison: solve_model vs solve_model2 ===")

    model1, overlap1 = solve_model_max_overlap(n, v, k)
    model2 = solve_model_total_overlap(n, v, k)

    if !has_values(model1) || !has_values(model2)
        println("One of the models has no primal solution; comparison unavailable.")
        return
    end

    x_model1 = round.(Int, value.(model1[:x]))
    x_model2 = round.(Int, value.(model2[:x]))

    overlaps_model1 = overlap_matrix(x_model1)
    overlaps_model2 = overlap_matrix(x_model2)

    max_overlap_model1 = maximum(overlaps_model1[i, j] for i in 1:n for j in i+1:n)
    max_overlap_model2 = maximum(overlaps_model2[i, j] for i in 1:n for j in i+1:n)

    println("Max pairwise overlap (solve_model): ", max_overlap_model1)
    println("Max pairwise overlap (solve_model2): ", max_overlap_model2)
    println("Gap (solve_model2 - solve_model) in max_overlap: ", max_overlap_model2 - max_overlap_model1)

    println("Rows where assignments differ:")
    diff_rows = [i for i in 1:n if any(x_model1[i, d] != x_model2[i, d] for d in 1:v)]
    if isempty(diff_rows)
        println("none")
    else
        println(join(diff_rows, ", "))
    end

    print_upper_triangular_overlap(overlaps_model1, "Upper-triangular overlap matrix (solve_model):")
    print_upper_triangular_overlap(overlaps_model2, "Upper-triangular overlap matrix (solve_model2):")
end

# Exemplo
n = 10
v = 25
k = 15


times = []
overlaps = []

N = [10]

for n in N
    start_time = time()
    model = solve_model_total_overlap(n, v, k)
    end_time = time()
    overlap_mat = overlap_matrix(round.(Int, value.(model[:x])))
    total_overlap = sum(overlap_mat[i, j] for i in 1:n for j in i+1:n)
    push!(overlaps, total_overlap)
    push!(times, end_time - start_time)
end

for i in eachindex(N)
    println("N = ", N[i], ": Time = ", times[i], " seconds, Total Overlap = ", overlaps[i])
end


# compare_solutions(n, v, k)
