# -*- coding: utf-8 -*-
"""Regenera as 4 figuras do artigo a partir dos CSVs reais
(reproducao/resultados/resultados_*.csv) para os 3 datasets:
Edge-IIoTset, TON_IoT, IoT-23. Saida em figures/ (PDF + PNG).

Ajustes de legibilidade:
* fig1: layout mais folgado, caixas com texto quebrado em linhas curtas;
* fig2: normalizacao de cor COMPARTILHADA entre os 6 paineis (vmax global),
        texto adaptativo (branco sobre celula escura, preto sobre clara);
* fig3: escala de cores clareada (vmin=0.40) + texto adaptativo;
* fig4: barras com rotulos de valor.
"""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.stdout.reconfigure(encoding="utf-8")
BASE = r"C:\Users\Carlos\Desktop\artigo_20260914"
RES = os.path.join(BASE, "reproducao", "resultados")
OUT = os.path.join(BASE, "figures")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi": 300,
})

BLUE = "#1f5fa8"; RED = "#c0392b"; GRAY = "#7f8c8d"
GREEN = "#27ae60"; ORANGE = "#e67e22"; PURPLE = "#6a1b9a"

DATASETS = ["Edge-IIoTset", "TON_IoT", "IoT-23"]
FILES = {"Edge-IIoTset": "resultados_edge_iiotset.csv",
         "TON_IoT": "resultados_ton_iot.csv",
         "IoT-23": "resultados_iot23_real.csv"}

def load():
    frames = []
    for ds, f in FILES.items():
        df = pd.read_csv(os.path.join(RES, f))
        df["Dataset"] = ds
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

def best_bal(sub):
    bal = sub[sub["Cenario"] != "Original (sem balancear)"].copy()
    mf1 = bal["F1-Score"].max()
    cand = bal[bal["F1-Score"] >= mf1 - 0.05]
    return cand.sort_values("FN").iloc[0]

def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, name + ".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("OK", name)

res = load()

# ------------------------------------------------------------------ FIG 1
def fig1_pipeline():
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    def box(x, y, w, h, text, fc="#eaf2fb", ec="#333333", fs=7.5, lw=1.0):
        ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3",
                                             fc=fc, ec=ec, lw=lw))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, linespacing=1.35)
    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#333333", lw=1.0))

    # linha 1: dados -> pre -> split
    box(1, 82, 27, 16, "3 datasets IoT/IIoT\nEdge-IIoTset · TON_IoT · IoT-23\n40.000 fluxos · 82% / 18%", fs=7.5)
    box(36, 82, 26, 16, "Pre-processamento\nStandardScaler\nSelectPercentile(60%)", fs=7.5)
    box(70, 82, 27, 16, "Split 70/30 (semente 42)\n28.000 treino / 12.000 teste", fs=7.5)
    arrow(28, 90, 36, 90); arrow(62, 90, 70, 90)

    # linha 2: seis estrategias
    labels = ["Original\n(sem balancear)", "SMOTETomek", "GAN+MLP", "WGAN-GP",
              "cWGAN-GP", "CTGAN"]
    y0, w, h = 48, 15.2, 15
    xs = []
    for i, lab in enumerate(labels):
        x = 2 + i * 16.2
        xs.append(x)
        box(x, y0, w, h, lab, fc="#fef9e7", ec=GRAY, fs=7.0)
        arrow(83, 82, x + w / 2, y0 + h)  # do split para cada estrategia

    # linha 3: classificadores -> avaliacao
    box(14, 8, 32, 15, "4 classificadores\nMLP · XGBoost\nRandom Forest · LSTM", fc="#eafaf1", fs=7.5)
    box(57, 8, 33, 15, "Avaliacao no teste fixo\nACC · Recall · F1\nTN / FP / FN / TP", fc="#eaf2fb", fs=7.5)
    # conexao estrategias -> linha central -> classificadores/avaliacao
    for xx in xs:
        arrow(xx + w / 2, y0 - 1, xx + w / 2, 29)
    arrow(30, 23, 30, 23 + 0.01)
    # barras coletoras curtas no centro e setas para as caixas
    ax.plot([xs[0] + w / 2, xs[-1] + w / 2], [29, 29], color="#333333", lw=0.8, zorder=0)
    arrow(26, 29, 26, 23)
    arrow(74, 29, 74, 23)
    ax.set_title("Experimental pipeline", fontsize=9, loc="left", pad=2)
    save(fig, "fig1_pipeline")

# ------------------------------------------------------------------ FIG 2
def fig2_confusion():
    mats = []
    panels = []
    for ds in DATASETS:
        sub = res[(res["Dataset"] == ds) & (res["Modelo"] == "LSTM")]
        base = sub[sub["Cenario"] == "Original (sem balancear)"].iloc[0]
        best = best_bal(sub)
        for row, tag in [(base, "Original"), (best, "Best balanced")]:
            m = np.array([[row["TN"], row["FP"]], [row["FN"], row["TP"]]])
            mats.append(m)
            panels.append((ds, tag, m))
    vmax = float(max(m.max() for m in mats))

    fig, axes = plt.subplots(3, 2, figsize=(7.6, 6.4),
                             gridspec_kw={"hspace": 0.5, "wspace": 0.3})
    letters = iter("abcdef")
    for r in range(3):
        for c in range(2):
            ds, tag, m = panels[r * 2 + c]
            ax = axes[r][c]
            im = ax.imshow(m, cmap="Blues", vmin=0, vmax=vmax, aspect="auto")
            ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
            ax.set_xticklabels(["Benign", "Malware"])
            ax.set_yticklabels(["Benign", "Malware"])
            ax.set_title(f"({next(letters)}) {ds}: {tag}", fontsize=8)
            for i in range(2):
                for j in range(2):
                    v = int(m[i, j])
                    fg = "white" if (v / vmax) > 0.55 else "black"
                    ax.text(j, i, f"{v:,}", ha="center", va="center",
                            fontsize=8.5, color=fg, fontweight="bold")
            ax.tick_params(axis="both", which="both", length=0)
    fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02)
    save(fig, "fig2_confusion")

# ------------------------------------------------------------------ FIG 3
def fig3_metrics():
    cen = ["Original (sem balancear)", "SMOTETomek", "GAN+MLP", "WGAN-GP",
           "cWGAN-GP", "CTGAN"]
    modelos = ["MLP", "XGBoost", "RandomForest", "LSTM"]
    vmin, vmax = 0.35, 1.0
    _norm = plt.Normalize(vmin, vmax)
    fig, axes = plt.subplots(1, 4, figsize=(8.8, 2.7),
                             gridspec_kw={"wspace": 0.32})
    for k, mdl in enumerate(modelos):
        piv = np.full((3, 6), np.nan)
        for i, ds in enumerate(DATASETS):
            for j, c in enumerate(cen):
                row = res[(res["Dataset"] == ds) & (res["Modelo"] == mdl)
                          & (res["Cenario"] == c)]
                if len(row):
                    piv[i, j] = row["F1-Score"].iloc[0]
        ax = axes[k]
        im = ax.imshow(piv, cmap="YlGnBu", vmin=vmin, vmax=vmax, aspect="auto")
        ax.set_xticks(range(6)); ax.set_xticklabels(cen, rotation=60, ha="right", fontsize=6.5)
        ax.set_yticks(range(3)); ax.set_yticklabels(["Edge", "TON", "IoT-23"], fontsize=7)
        ax.set_title(mdl, fontsize=8)
        for i in range(3):
            for j in range(6):
                v = piv[i, j]
                if np.isnan(v):
                    continue
                rgba = plt.cm.YlGnBu(_norm(v))
                lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
                fg = "black" if lum > 0.55 else "white"
                ax.text(j, i, f"{v:.3f}", ha="center", va="center",
                        fontsize=6, color=fg, rotation=90)
    fig.suptitle("F1-score per dataset, model, and balancing strategy", fontsize=10, y=1.04)
    fig.colorbar(im, ax=axes, fraction=0.02, pad=0.02)
    save(fig, "fig3_metrics")

# ------------------------------------------------------------------ FIG 4
def fig4_fnfptp():
    cen = ["Original (sem balancear)", "SMOTETomek", "GAN+MLP", "WGAN-GP",
           "cWGAN-GP", "CTGAN"]
    modelos = ["MLP", "XGBoost", "RandomForest", "LSTM"]
    cores = [BLUE, ORANGE, GREEN, PURPLE]
    fig, axes = plt.subplots(1, 3, figsize=(8.8, 2.7), sharey=True,
                             gridspec_kw={"wspace": 0.06})
    x = np.arange(len(cen)); w = 0.2
    for a, ds in enumerate(DATASETS):
        ax = axes[a]
        sub = res[res["Dataset"] == ds]
        YTICK = 2000.0   # escala visivel (ticks) ate 2000
        YLIM = 2280.0    # folga extra acima p/ caber o rotulo vertical (~4 digitos)
        for k, mdl in enumerate(modelos):
            fns = [sub[(sub["Modelo"] == mdl) & (sub["Cenario"] == c)]["FN"].iloc[0]
                   for c in cen]
            ax.bar(x + (k - 1.5) * w, fns, w, label=mdl, color=cores[k])
            for xi, v in zip(x + (k - 1.5) * w, fns):
                if v:
                    ax.text(xi, v + 0.012 * YTICK, f"{int(v)}", ha="center", va="bottom",
                            fontsize=5.5, rotation=90, color="#222222")
        ax.set_yticks([0, 500, 1000, 1500, 2000])
        ax.set_xticks(x); ax.set_xticklabels(cen, rotation=60, ha="right", fontsize=6.5)
        ax.set_title(ds, fontsize=8)
        ax.set_ylim(0, YLIM)
        if a == 0:
            ax.set_ylabel("False negatives")
        ax.legend(frameon=False, fontsize=6, ncol=2)
    fig.suptitle("False negatives per model and balancing strategy (fixed test set)", fontsize=10, y=1.05)
    save(fig, "fig4_fnfptp")

# ------------------------------------------------------------------ FIG 5
TT = {"GAN": {"Edge-IIoTset": 971, "TON_IoT": 1280, "IoT-23": 953},
       "WGAN-GP": {"Edge-IIoTset": 222, "TON_IoT": 207, "IoT-23": 211},
       "cWGAN-GP": {"Edge-IIoTset": 273, "TON_IoT": 253, "IoT-23": 265},
       "CTGAN": {"Edge-IIoTset": 321, "TON_IoT": 282, "IoT-23": 130}}
GEN_OF = {"Original (sem balancear)": None, "SMOTETomek": None,
          "GAN+MLP": "GAN", "WGAN-GP": "WGAN-GP",
          "cWGAN-GP": "cWGAN-GP", "CTGAN": "CTGAN"}
CEN5 = list(GEN_OF.keys())

def fig5_fntt():
    st = {"Original (sem balancear)": ("o", GRAY, 34),
          "SMOTETomek": ("*", GREEN, 90),
          "GAN+MLP": ("X", RED, 40),
          "WGAN-GP": ("o", BLUE, 34),
          "cWGAN-GP": ("s", ORANGE, 26),
          "CTGAN": ("^", PURPLE, 30)}
    fig, axes = plt.subplots(1, 3, figsize=(8.8, 2.7), sharey=False,
                             gridspec_kw={"wspace": 0.34})
    for a, ds in enumerate(DATASETS):
        ax = axes[a]
        sub = res[(res["Dataset"] == ds) & (res["Modelo"] == "LSTM")]
        for c in CEN5:
            fn = int(sub[sub["Cenario"] == c]["FN"].iloc[0])
            g = GEN_OF[c]
            tt = TT[g][ds] if g else 0
            mk, col, s = st[c]
            ax.scatter(tt, fn, marker=mk, s=s, color=col, edgecolors="#222222", lw=0.5, zorder=3)
            lab = {"Original (sem balancear)": "Orig", "SMOTETomek": "SMOTE"}.get(c, c)
            dy = 26 if c == "GAN+MLP" else (10 if c == "Original (sem balancear)" else 8)
            ax.annotate(lab, (tt, fn), xytext=(6, dy), textcoords="offset points",
                        fontsize=6, color="#222222")
        ax.set_xlim(-30, 1360)
        ax.set_xlabel("TT (s)")
        ax.set_title(ds, fontsize=8)
        if a == 0:
            ax.set_ylabel("LSTM FN (test set)")
    fig.suptitle("LSTM cost-effectiveness: FN on the test set vs. generator training time", fontsize=9.5, y=1.04)
    save(fig, "fig5_fntt")

fig1_pipeline()
fig2_confusion()
fig3_metrics()
fig4_fnfptp()
fig5_fntt()
print("All figures generated.")