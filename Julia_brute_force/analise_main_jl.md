# Análise do `main.jl`

## O que o código faz

O arquivo implementa dois modelos de **Programação Inteira Mista (MIP)** em Julia,
usando JuMP como interface de modelagem e Gurobi (ou HiGHS) como solver.
O objetivo é selecionar `n` bilhetes da Lotofácil de forma a minimizar o
overlap entre eles — o mesmo objetivo do Simulated Annealing descrito no artigo,
mas resolvido de forma **exata** em vez de heurística.

---

## Variáveis de decisão

Para `n` bilhetes sobre um universo `[v]` com `k` dezenas por bilhete:

| Variável | Domínio | Significado |
|---|---|---|
| `x[i, d]` | `{0, 1}` | bilhete `i` contém a dezena `d` |
| `z[i, j, d]` | `[0, 1]` | produto `x[i,d] * x[j,d]` (linearizado) |
| `M` | `≥ 0` | overlap máximo entre qualquer par (só no modelo 1) |

A linearização do produto `x[i,d] * x[j,d]` usa as três restrições clássicas
de McCormick, que são exatas para variáveis binárias:

```
z[i,j,d] ≤ x[i,d]
z[i,j,d] ≤ x[j,d]
z[i,j,d] ≥ x[i,d] + x[j,d] − 1
```

---

## Os dois modelos

### Modelo 1 — `solve_model_max_overlap`

Minimiza o overlap **máximo** entre qualquer par de bilhetes (formulação minimax):

```
min  M
s.t. Σ_d z[i,j,d] ≤ M    para todo par (i,j)
```

Pergunta que responde: "qual a coleção de `n` bilhetes em que o par com maior
overlap tem o menor overlap possível?"

### Modelo 2 — `solve_model_total_overlap`

Minimiza o overlap **total** entre todos os pares:

```
min  Σ_{i<j} Σ_d z[i,j,d]
```

Essa é exatamente a mesma função objetivo `Ω(A)` que o Simulated Annealing
do artigo tenta minimizar. A diferença é que aqui a solução é **ótima garantida**.

---

## Quebras de simetria

O problema tem muitas soluções equivalentes por permutação de bilhetes e
relabeling das dezenas. O código adiciona dois cortes para reduzir o espaço:

1. **Fixa o primeiro bilhete** como `{1, 2, ..., k}`:
   ```julia
   x[1, d] == 1  para d = 1..k
   x[1, d] == 0  para d = k+1..v
   ```

2. **Ordena colunas por frequência decrescente**:
   ```julia
   Σ_i x[i, d] >= Σ_i x[i, d+1]  para d = 1..v-1
   ```

Essas restrições não alteram o valor ótimo — apenas eliminam soluções
simétricas, acelerando a busca do solver.

---

## Tamanho do problema para a Lotofácil (v=25, k=15)

| `n` | Vars binárias (`x`) | Vars contínuas (`z`) | Restrições de linearização |
|---|---|---|---|
| 5  | 125 | 1.500 | 1.500 |
| 10 | 250 | 11.250 | 11.250 |
| 20 | 500 | 47.500 | 47.500 |
| 50 | 1.250 | 306.250 | 306.250 |

Para `n=10`, o Gurobi resolve em segundos. Para `n≥30`, o tempo pode
crescer rapidamente dependendo da qualidade dos relaxamentos LP.

---

## Comparação com o Greedy + SA do artigo

| Critério | IP (Julia) | Greedy + SA (Python) |
|---|---|---|
| Qualidade da solução | **Ótima exata** para Ω | Aproximada — heurística |
| Garantia teórica | Ótimo global | `(1−1/e)` para cobertura + SA sem garantia |
| Complexidade | NP-hard em geral | O(n·M·v) — linear em n |
| n=10, v=25 | ~segundos (Gurobi) | <0.1 s |
| n=100, v=25 | minutos/horas | <1 s |
| Calcula P(ganhar) | Não | Sim (Monte Carlo) |
| Conecta com probabilidade | Não | Sim |

O IP é mais poderoso para `n` pequeno e dá a resposta exata. O Greedy + SA
é necessário para `n` grande e para integrar a estimativa de `P_win`.

---

## Uso potencial para validar o artigo

O IP resolve exatamente o mesmo sub-problema que o SA aproxima. Isso abre
uma validação empírica valiosa: rodar o IP para `n ≤ 10` e comparar o valor
de `Ω` com o que o SA encontra. Se os valores forem iguais (ou muito próximos),
isso confirma que o SA é de alta qualidade na prática — mesmo sem garantia
teórica para `n > 2`.

Sugestão de experimento:

```julia
for n in [2, 3, 5, 7, 10]
    Ω_ip  = solve_model_total_overlap(n, 25, 15)  # ótimo exato
    Ω_sa  = ...                                     # resultado do SA Python
    gap   = (Ω_sa - Ω_ip) / Ω_ip * 100
    println("n=$n: Ω_IP=$Ω_ip, Ω_SA=$Ω_sa, gap=$(gap)%")
end
```

---

## Bugs encontrados

### Bug 1 — `compare_solutions` quebra em runtime

```julia
# linha 155 — ERRO: solve_model_max_overlap retorna só model, não (model, overlap)
model1, overlap1 = solve_model_max_overlap(n, v, k)
```

`solve_model_max_overlap` retorna apenas `model`. A desestruturação em dois
valores causará `BoundsError` ao executar `compare_solutions`. Correção:

```julia
model1 = solve_model_max_overlap(n, v, k)
x1 = round.(Int, value.(model1[:x]))
overlap1 = overlap_matrix(x1)
```

### Bug 2 — overlap_matrix conta a diagonal (desnecessário)

```julia
function overlap_matrix(x)
    for i in 1:n
        for j in 1:n   # ← inclui i==j (sobreposição do bilhete com ele mesmo = k)
```

A diagonal dá `k=15` para todo `i`, o que é correto matematicamente mas
pode confundir se a matriz for usada para calcular o overlap total.
Considere usar apenas `j > i` ou zerar a diagonal.

### Bug 3 — `solve_model_max_overlap` não retorna o overlap

Internamente computa `overlap` mas não o retorna — a função devolve apenas
`model`. Qualquer chamador que precise do overlap tem de recomputá-lo fora,
o que é redundante.

---

## Resumo

O `main.jl` **não implementa** as otimizações do artigo (Greedy, SA, Monte Carlo,
estimativa de P_win). Ele resolve um sub-problema mais restrito — a minimização
exata de Ω — usando IP. As duas abordagens são complementares:

- **IP (Julia)**: referência de qualidade para `n` pequeno; útil para validar o SA.
- **Greedy + SA (Python)**: escala para `n` grande; conectado à análise probabilística completa.
