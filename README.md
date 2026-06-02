# Coverage Maximization and Overlap Minimization for Multi-Ticket Lottery Selection

Companion repository for the paper:

> **Coverage Maximization and Overlap Minimization for Multi-Ticket Lottery Selection:
> Theory, Algorithms, and Empirical Validation**
>
> Lucas Rafael de Andrade (UERJ -- PPGCE) &
> Victor Hugo Nascimento (FGV -- School of Applied Mathematics)

## Contents

| File | Description |
|---|---|
| `paper/main.tex` | LaTeX source (main document) |
| `paper/sec*.tex` | Individual sections |
| `paper/refs.bib` | Bibliography (all references verified) |
| `lotofacil_optimizer.py` | Greedy Coverage Selection + Simulated Annealing |
| `benchmark.py` | Paired Monte Carlo benchmark (random vs greedy vs SA) |
| `benchmark_extended.py` | Extended benchmark for n up to 100 |
| `low_energy_hypothesis.py` | Preliminary consecutive-pairs analysis |
| `benchmark_results*.csv` | Raw benchmark data |
| `benchmark_summary*.csv` | Aggregated results |
| `benchmark_plot*.png` | Result figures |

## Reproducing the results

```bash
# Install dependencies
pip install numpy pandas matplotlib scipy tqdm

# Run the benchmark (produces benchmark_results.csv and benchmark_plot.png)
python benchmark.py

# Run extended benchmark (n up to 100)
python benchmark_extended.py

# Generate optimised tickets (example)
python -c "
from lotofacil_optimizer import generate_apostas
r = generate_apostas(n_bilhetes=5, modo_otimizacao='annealing', seed=42)
for i, b in enumerate(r['bilhetes']):
    print(f'B{i+1}: {b}')
print(f\"P(>=11): {r['probabilidade_>=11']}\")
"
```

## Authors

**Lucas Rafael de Andrade**
UERJ -- Programa de Pós-Graduação em Ciências Econômicas (PPGCE)
rafael.lucas@posgraduacao.uerj.br

**Victor Hugo Nascimento**
School of Applied Mathematics, FGV
Praia de Botafogo, Rio de Janeiro, Brazil
