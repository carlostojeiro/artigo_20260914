# Séries de Aulas 6–8 — Expansão Multi-Dataset (UNSW-NB15, CICIDS2017) + 4 Classificadores

Continuação do estudo *"Reducing False Negatives in IoT Malware Detection"* (aulas 1–5, IoT-23).
Objetivo: repetir a mesma ideia (6 cenários de balanceamento: Original, SMOTETomek, GAN+MLP,
WGAN-GP, cWGAN-GP, CTGAN) em **datasets públicos reais** e com **4 classificadores**
(MLP, XGBoost, RandomForest, LSTM), reportando sempre FN/FP/TP/TN.

## Ordem de execução (no Google Colab)

| Ordem | Notebook | O que faz | Saída |
|---|---|---|---|
| 1 | `aula_iot23_unsw_nb15.ipynb` | UNSW-NB15 real (175.341 fluxos) → amostra 40.000 (82/18) → 6 cenários × 4 modelos | `resultados_unsw_nb15.csv` |
| 2 | `aula_iot23_cicids2017.ipynb` | CICIDS2017 real (8 CSVs diários, ~2,8M fluxos) → mesma malha | `resultados_cicids2017.csv` |
| 3 | `aula_iot23_consolidacao.ipynb` | Junta os CSVs + (opcional) recalcula IoT-23 com os 4 modelos | `resultados_consolidados.csv` + figuras |

## Como rodar

1. Vá em https://colab.research.google.com → **Upload** de cada notebook.
2. **Runtime → Run all** (Recomendado: Runtime → Change runtime type → **T4 GPU**).
   - Tempo estimado por notebook de dataset: **30–60 min** (treino de 4 GANs × 300 épocas + 24 fits de classificador).
3. Ao final, cada notebook baixa automaticamente seu CSV de resultados. Guarde os CSVs
   (`resultados_unsw_nb15.csv`, `resultados_cicids2017.csv`) para a aula de consolidação.
4. Na consolidação: faça upload dos 2 CSVs → (opcional) rode a seção do IoT-23 → tabelas/figuras finais.

## Downloads dos datasets (embutidos nos notebooks, com fallback)

- **UNSW-NB15:** `UNSW_NB15_training-set.csv` (32 MB) — mirror público no HuggingFace do dataset oficial (CC BY 4.0).
- **CICIDS2017:** 8 arquivos diários `MachineLearningCSV` (~960 MB no total) — mirror público no HuggingFace.
- Se um download falhar: baixe manualmente e faça **upload para `/content/`** (o notebook detecta o arquivo existente).

## Protocolo (idêntico ao IoT-23, para comparação justa)

- Amostra estratificada **40.000 registros**, **82% benigno / 18% ataque** (semente 42).
- Split 70/30 estratificado (mesmo teste para todos os cenários e modelos).
- `StandardScaler` → `SelectPercentile(60%)` (f_classif).
- Balanceamento até 1:1 para SMOTETomek, GAN+MLP, WGAN-GP, cWGAN-GP e CTGAN.
- Sementes fixas: `np.random.seed(42)`, `tf.random.set_seed(42)`.

## Transparência científica (LEIA)

- **Aulas 1–5 (IoT-23):** usavam uma **amostra sintética representativa** do IoT-23 (gerada com
  distribuições estatísticas dos fluxos reais, para fins didáticos). Mantida no artigo como está,
  mas documentada.
- **Aulas 6–7 (UNSW-NB15, CICIDS2017):** datasets **reais**, mas o UNSW-NB15 tem ataque como
  classe majoritária no arquivo original — por isso a **amostragem estratificada 82/18** é um
  protocolo declarado (não ocultação) para espelhar o IoT-23. Isso deve ser escrito no artigo.
- O notebook de consolidação recalcula o **IoT-23 com os 4 classificadores** (seção opcional),
  deixando a comparação de 3 datasets 100% homogênea: Dataset × Modelo × Cenário.

## Como alimentar o artigo

- Copie os números das tabelas da aula 8 para o `main.tex` (Tabela I) e as figuras para o `make_figures_v2.py`.
- Se o CTGAN reduzir FN/FP nos 3 datasets (e para os 4 modelos), o principal argumento do artigo
  (efeito do balanceamento, não do classificador) fica muito mais forte para um periódico como
  IEEE Sensors / Sensors (MDPI).

## Arquivos da série

- `aula_iot23_unsw_nb15.ipynb` — Aula 6
- `aula_iot23_cicids2017.ipynb` — Aula 7
- `aula_iot23_consolidacao.ipynb` — Aula 8
- Gerador: `C:\Users\Carlos\AppData\Local\Temp\opencode\build_aulas.py` + `nbkit.py`
  (se quiser regenerar/ajustar os notebooks, rode `build_aulas.py` no Python do PC).