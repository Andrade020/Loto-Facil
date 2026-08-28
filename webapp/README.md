# Prisma — Web App

Aplicação web que transforma o método do artigo *"Coverage Maximization and
Overlap Minimization for Multi-Ticket Lottery Selection"* num produto: para um
orçamento de **N bilhetes**, gera a carteira de apostas que **maximiza a chance
de prêmio** em Lotofácil, Mega-Sena, Quina, Lotomania, Dupla Sena e Dia de
Sorte.

100% no navegador — sem backend, sem coleta de dados. Todo o cálculo (geração de
pool, seleção gulosa, simulated annealing e Monte Carlo) roda numa Web Worker.

Identidade visual "Prisma": paleta oklch (hue de fundo 260, hue de acento 275),
tipografia Newsreader (display, itálico) + IBM Plex Sans (corpo), tokens em
`src/styles.css`. Roteamento por hash sem dependência (`src/useHashRoute.ts`)
entre a home (`src/components/ToolPage.tsx`) e a página explicativa
`src/components/ComoFunciona.tsx`, que usa números *reais* (não ilustrativos)
gerados chamando `optimize()` de verdade — ver comentário no topo do arquivo
para reproduzir.

## Como funciona (resumo)

Para uma loteria "escolha `k` dezenas de um universo de `v`; ganha quem acertar
`≥ t` das `d` sorteadas":

1. **Pool** de bilhetes candidatos aleatórios distintos.
2. **Greedy Max-Coverage** — a cada passo escolhe o bilhete que cobre mais
   dezenas ainda não cobertas (garantia 1 − 1/e; Nemhauser et al., 1978).
3. **Simulated Annealing** — refina minimizando a sobreposição total
   `Σ|Aᵢ∩Aⱼ|`. Menos sobreposição ⇒ bilhetes anti-correlacionados ⇒ maior
   `P(≥ t em algum bilhete)`. O delta de cada troca é `colCount[add] −
   colCount[rem] + 1` (identidade `Ω = Σ_d C(freq(d),2)` do artigo).
4. **Monte Carlo** — estima `P(≥ t)` simulando sorteios do universo completo.

A carteira otimizada **supera** a baseline de bilhetes independentes/aleatórios
(`1 − (1 − p)ⁿ`) justamente por essa anti-correlação — exatamente a tese do
artigo. As métricas mostram a sobreposição obtida vs. o ótimo teórico `Ω*`.

Suporta **dezenas fixas** (entram em todos os bilhetes) e **excluídas** (nunca
aparecem); a otimização opera no espaço livre restante.

O jogador também pode **incluir as próprias apostas completas** ("minhas
apostas"): elas entram na carteira como estão e os bilhetes gerados são
escolhidos para minimizar a sobreposição também com elas (via baseline
`seedColCount` no greedy e no SA).

Tema **claro por padrão**, seguindo a preferência do navegador
(`prefers-color-scheme`), com alternância manual persistida.

## Rodar localmente

```bash
cd webapp
npm install
npm run dev      # servidor de desenvolvimento (http://localhost:5173)
npm test         # self-test do otimizador (sem navegador)
npm run build    # build de produção em dist/
npm run preview  # serve o build
```

## Deploy

`dist/` é estático — publique em Vercel, Netlify, Cloudflare Pages ou GitHub
Pages. O `base: "./"` no `vite.config.ts` já funciona em subdiretórios.

## Adicionar uma loteria

Inclua uma entrada em `src/lotteries.ts` com `universe`, `draw`, `minPick`,
`maxPick`, `premioMin` e `basePrice`. O otimizador é genérico — nada mais muda.
Campos opcionais: `draws` (sorteios independentes por concurso, ex. Dupla Sena
= 2 — ganha acertando o limiar em qualquer um), `numberOffset` (deslocamento de
exibição, ex. Lotomania mostra 00–99 pra um universo interno 1–100) e
`notaPremiacao` (aviso de faixa de prêmio real que a otimização não cobre, ex.
"acertar zero" da Lotomania ou o Mês da Sorte do Dia de Sorte).

## Atualizar preços

Os preços em `src/lotteries.ts` (`basePrice`) são os vigentes após o reajuste
das Loterias CAIXA de 09/07/2025. Confira em loterias.caixa.gov.br e atualize
quando houver novo reajuste. Custo de aposta com mais dezenas =
`basePrice × C(marcadas, mínimo)`.

## Aviso

Ferramenta independente, sem vínculo com a Caixa. Loteria tem valor esperado
negativo: o otimizador distribui melhor o risco do orçamento, **não** prevê
resultados nem altera as probabilidades do sorteio. +18.
