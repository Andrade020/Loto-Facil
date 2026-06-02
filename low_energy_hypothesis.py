import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt

FILE = r"C:\Users\LucasRafaeldeAndrade\Desktop\Repositorios\Loto-Facil\loto_facil_asloterias_ate_concurso_3513_sorteio.xlsx"

def find_header_row(path):
    tmp = pd.read_excel(path, header=None, nrows=30)
    for r in range(tmp.shape[0]):
        row_vals = tmp.iloc[r].astype(str).str.lower().tolist()
        if any("concurso" in v for v in row_vals):
            return r
        cnt_bola = sum(bool(re.search(r"\b(bola|dezena)\b", v)) for v in row_vals)
        if cnt_bola >= 6:
            return r
    return 0

def load_draws(path):
    header_row = find_header_row(path)
    print(f"Detected header row: {header_row} (0-indexed). Reading with header={header_row}.")
    df = pd.read_excel(path, header=header_row)
    pattern = re.compile(r"\b(bola|dezena)\b\s*\D*?(\d{1,2})", flags=re.IGNORECASE)
    bola_cols = [c for c in df.columns if pattern.search(str(c))]
    if len(bola_cols) < 15:
        numeric_candidates = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and df[c].dropna().between(1,25).all()]
        numeric_candidates = sorted(numeric_candidates, key=lambda x: str(x))
        if len(numeric_candidates) >= 15:
            bola_cols = numeric_candidates[:15]
    if len(bola_cols) < 15:
        raise ValueError(f"Não encontrei 15 colunas de dezenas. Encontradas: {bola_cols}")
    print(f"Detected ball columns (count={len(bola_cols)}): {bola_cols}")
    sub = df[bola_cols]
    mask = sub.notna().all(axis=1)
    arr = sub[mask].astype(int).values
    sorteios = np.sort(arr, axis=1).tolist()
    return sorteios, bola_cols, header_row

if __name__ == "__main__":
    sorteios, bola_cols, header_row = load_draws(FILE)
    print(f"Loaded {len(sorteios)} draws. Sample draw: {sorteios[0]}")

    # np.diff sobre array ordenado conta pares consecutivos sem loops Python
    sorteios_arr = np.array(sorteios)
    pares_obs_list = np.sum(np.diff(sorteios_arr, axis=1) == 1, axis=1)
    pares_obs = float(pares_obs_list.mean())
    print(f"Observed mean consecutive-pairs per draw: {pares_obs:.4f}")

    N_SIM = 500_000  # 25x mais precisão; termina em frações de segundo
    rng = np.random.default_rng()

    # Gera todas as amostras de uma vez: N_SIM linhas, cada uma é uma permutação
    # aleatória de {1..25} da qual tomamos os 15 primeiros índices — equivalente
    # exato a np.random.choice(25, replace=False), mas 100% vetorizado.
    samples = rng.random((N_SIM, 25)).argsort(axis=1)[:, :15] + 1
    samples.sort(axis=1)
    sims = np.sum(np.diff(samples, axis=1) == 1, axis=1)

    media_nula = sims.mean()
    p_valor = np.mean(sims >= pares_obs)
    print(f"Simulated null mean: {media_nula:.4f}")
    print(f"p-value (H1 = accumulation): {p_valor:.6f}")

    plt.figure(figsize=(8, 4))
    plt.hist(sims, bins=range(sims.min(), sims.max() + 2), alpha=0.7)
    plt.axvline(pares_obs, color='red', linewidth=2, label=f'Observed = {pares_obs:.2f}')
    plt.xlabel('Number of consecutive pairs per draw')
    plt.ylabel('Frequency')
    plt.title('Null distribution vs observed')
    plt.legend()
    plt.tight_layout()
    plt.show()
