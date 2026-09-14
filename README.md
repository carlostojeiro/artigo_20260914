# Reducing False Negatives in IoT Malware Detection

**Reducing False Negatives in IoT Malware Detection: A Comparative Study of Generative
Oversampling on the IoT-23 Dataset** â€” artigo cientÃ­fico IEEE (IEEEtran, journal), alvo
candidato **IEEE Internet of Things Journal (IoT-J)**.

Reexecuta os experimentos das aulas 1-8 e gera o pacote Overleaf do manuscrito.

## Estrutura

```
artigo_iot23/
â”œâ”€â”€ main.tex                  # Artigo final (Spring International IEEEtran) â€” fonte Ãºnica
â”œâ”€â”€ references.bib
â”œâ”€â”€ figures/                  # Figuras PDF (vetoriais) + PNG â€” geradas por make_figures_v2.py
â”œâ”€â”€ make_figures_v2.py        # Gera as 4 figuras do artigo
â”œâ”€â”€ overleaf/                 # .zip pronto para Overleaf (ver zip_overleaf.py)
â”œâ”€â”€ reproducao/
â”‚   â”œâ”€â”€ artigo_iot23_main_PT.md          # TraduÃ§Ã£o integral PT-BR espelhada ao main.tex
â”‚   â”œâ”€â”€ notebooks/                       # Os 4 notebooks de Colab (dataset + consolidaÃ§Ã£o)
â”‚   â”œâ”€â”€ resultados/                      # TODOS os CSVs de resultados (raw + tabelas finais)
â”‚   â””â”€â”€ docs/                            # LEIA-ME da sÃ©rie de aulas, suplementos, etc.
â””â”€â”€ README.md
```

## Compilar (duas formuladas)

1. `python make_figures_v2.py` (opcional, se regenerar figuras).
2. `python zip_overleaf.py` â†’ gera `overleaf/artigo_iot23_overleaf.zip` (main.tex + bib + figures +
   suplementos).
3. Envie o zip ao Overleaf (Upload Project), compile **duas vezes** com **BibTeX** no meio
   (PDFLaTeX). Alternativa local: TeX Live + `pdflatex main` â†’ `bibtex main` â†’ `pdflatex main` Ã—2.

## ReproduÃ§Ã£o dos experimentos (Google Colab, ordem)

1. `aula_iot23_cicids2017.ipynb` â†’ `resultados_cicids2017.csv` (+ `tempos_treino_cicids2017.csv`)
2. `aula_iot23_unsw_nb15.ipynb` â†’ `resultados_unsw_nb15.csv` (+ `tempos_treino_unsw_nb15.csv`)
3. `aula_iot23_real.ipynb` â†’ `resultados_iot23_real.csv` (+ `tempos_treino_iot23_real.csv`)
4. `aula_iot23_consolidacao.ipynb` â†’ consolida os 3 datasets (Ãºltimo a rodar)

Cada notebook baixa automaticamente seus CSVs (Colab â†’ aba Arquivos). Os CSVs de resultados
vÃ£o para `reproducao/resultados/` e os suplementos (tabelas de IC95/sensibilidade/tempos) para
`reproducao/supplementary/`.

## Datasets

- **CICIDS2017 / UNSW-NB15:** arquivos pÃºblicos (mirror HuggingFace), ~40.000 fluxos amostrados
  estratificados (82% benigno / 18% ataque, semente 42), split 70/30.
- **IoT-23:** amostra sintÃ©tica representativa (notebooks didÃ¡ticos aulas 1-5), mesma malha de
  cenÃ¡rios para comparaÃ§Ã£o homogÃªnea.

TransparÃªncia e limitaÃ§Ãµes documentadas em `main.tex` Â§"Threats to Validity" e no LEIA-ME.
