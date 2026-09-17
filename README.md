# Reduzindo Falsos Negativos na Detecção de Malware IoT

**Reducing False Negatives in IoT Malware Detection: A Comparative Study of Generative
Oversampling on the IoT-23 Dataset** — artigo científico IEEE (IEEEtran, journal), alvo
candidato **IEEE Internet of Things Journal (IoT-J)**.

Reexecuta os experimentos das aulas 1-8 e gera o pacote Overleaf do manuscrito.

## Estrutura

```
artigo_20260914/
|-- main.tex                  # Artigo final (Spring International IEEEtran) — fonte única
|-- references.bib
|-- figures/                  # Figuras PDF (vetoriais) + PNG — geradas por make_figures_v2.py
|-- make_figures_v2.py        # Gera as 4 figuras do artigo
|-- overleaf/                 # .zip pronto para Overleaf (ver zip_overleaf.py)
|-- reproducao/
|   |-- artigo_iot23_main_PT.md          # Tradução integral PT-BR espelhada ao main.tex
|   |-- notebooks/                       # Os 4 notebooks de Colab (dataset + consolidação)
|   |-- resultados/                      # TODOS os CSVs de resultados (raw + tabelas finais)
|   `-- docs/                            # LEIA-ME da série de aulas, suplementos, etc.
`-- README.md
```

## Compilar (duas formuladas)

1. `python make_figures_v2.py` (opcional, se regenerar figuras).
2. `python zip_overleaf.py` -> gera `overleaf/artigo_iot23_overleaf.zip` (main.tex + bib + figures +
   suplementos).
3. Envie o zip ao Overleaf (Upload Project), compile **duas vezes** com **BibTeX** no meio
   (PDFLaTeX). Alternativa local: TeX Live + `pdflatex main` -> `bibtex main` -> `pdflatex main` ×2.

## Reprodução dos experimentos (Google Colab, ordem)

1. `aula_edge_iiotset.ipynb` -> `resultados_edge_iiotset.csv` (+ `tempos_treino_edge_iiotset.csv`
   + `resultados_oof10_edge_iiotset.csv`)
2. `aula_ton_iot.ipynb` -> `resultados_ton_iot.csv` (+ `tempos_treino_ton_iot.csv`
   + `resultados_oof10_ton_iot.csv`)
3. `aula_iot23_real.ipynb` -> `resultados_iot23_real.csv` (+ `tempos_treino_iot23_real.csv`
   + `resultados_oof10_iot23_real.csv`)
4. `aula_iot23_consolidacao.ipynb` -> consolida os 3 datasets (último a rodar)

Cada notebook baixa automaticamente seus CSVs (Colab -> aba Arquivos). Os CSVs de resultados
vão para `reproducao/resultados/` e os suplementos (tabelas de IC95/sensibilidade/tempos) para
`reproducao/supplementary/`.

As aulas 6-7 foram **reescopadas para datasets IoT/IIoT reais** (decisão registrada na sessão):
`aula_iot23_cicids2017.ipynb` e `aula_iot23_unsw_nb15.ipynb` (UNSW-NB15, CICIDS2017 — datasets de
rede geral, não-IoT) ficam como **legado** e não alimentam mais o manuscrito.

## Datasets

- **Edge-IIoTset** (IEEE Access 2022): testbed IoT/IIoT de 7 camadas, 61 features, 14 ataques.
  Arquivo oficial `DNN-EdgeIIoT-dataset.csv` (2.219.201 x 63) via Kaggle/IEEE DataPort; o
  notebook baixa com o seu `kaggle.json` (Kaggle CLI) ou aceita upload manual do CSV.
- **TON_IoT** (IEEE Access 2020, UNSW Canberra): dataset de rede IoT/IIoT (Zeek/Argus) com
  `label` binário e `type` multiclasse; mirror público no HuggingFace com fallback.
- **IoT-23** (Stratosphere Lab): flow features do `conn.log` via mirror preprocessado.
- Todos reduzidos à mesma carga de **40.000 fluxos, 82% benigno / 18% ataque** (semente 42),
  split 70/30 — protocolo controlado idêntico para comparação direta.

Transparência e limitações documentadas em `main.tex` §"Threats to Validity" e no LEIA-ME.
