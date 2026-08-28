export const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export const pct = (v: number, casas = 2) =>
  (v * 100).toLocaleString("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  }) + "%";

/**
 * Probabilidade em linguagem de "chance": "1 em N" quando arredonda bem
 * (ex.: 35% -> "1 em 3"); para chances altas, onde "1 em 1" ficaria sem
 * sentido, usa "X em 10" (ex.: 80% -> "8 em 10").
 */
export const umEm = (p: number) => {
  if (p <= 0) return "—";
  if (p >= 1) return "praticamente certo";
  const n = Math.round(1 / p);
  if (n <= 1) {
    // chance alta: "X em 10"
    const x = Math.min(9, Math.max(1, Math.round(p * 10)));
    return `${x} em 10`;
  }
  return "1 em " + n.toLocaleString("pt-BR");
};

export const dd = (n: number) => String(n).padStart(2, "0");
