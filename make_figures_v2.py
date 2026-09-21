# -*- coding: utf-8 -*-
"""Regenera as 4 figuras do artigo a partir dos CSVs reais
(reproducao/resultados/resultados_*.csv) para os 3 datasets:
Edge-IIoTset, TON_IoT, IoT-23. Saida em figures/ (PDF + PNG).
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
RES  = os.path.join(BASE, "reproducao", "resultados")
OUT  = os.path.join(BASE, "figures")
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
    """Menor FN entre os 5 cenarios balanceados com F1 dentro de 0.05 do
    melhor F1 balanceado (regra do artigo)."""
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
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 110)
    def box(x, y, w, h, text, fc="#eaf2fb", ec="#333333", fs=8):
        ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                                             fc=fc, ec=ec, lw=1.0))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)
    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#333333", lw=1.1))
    box(1, 78, 26, 20, "Three IoT/IIoT datasets\nEdge-IIoTset - TON_IoT - IoT-23\n40,000 flows: 82% benign / 18% attack", fs=8)
    box(29, 78, 30, 20, "Preprocessing\nStandardScaler + \nSelectPercentile (60%)", fs=8)
    box(61, 78, 18, 20, "Split 70/30 stratified\n(seed 42)\n28,000 / 12,000", fs=8)
    arrow(27, 88, 29, 88); arrow(59, 88, 61, 88)
    labels = ["Original\n(no balancing)", "SMOTETomek", "GAN+MLP", "WGAN-GP",
              "cWGAN-GP", "CTGAN"]
    y0, w, h = 46, 14.8, 20
    for i, lab in enumerate(labels):
        box(2 + i * (w + 1.0), y0, w, h, lab, fc="#fef9e7", ec=GRAY)
    arrow(66, 78, 66, 67)
    for i in range(6):
        x = 2 + i * (w + 1.0)
        arrow(60, 65, x + w / 2, y0 + h + 1)
    box(26, 8, 22, 15, "MLP / XGBoost /\nRandom Forest / LSTM", fc="#eafaf1")
    box(56, 8, 28, 15, "Evaluation on fixed test set\nACC, Recall, F1, TN/FP/FN/TP", fc="#eaf2fb")
    for i in range(6):
        x = 2 + i * (w + 1.0)
        arrow(x + w / 2, y0 - 1, 37, 23)
    arrow(48, 15.5, 56, 15.5)
    ax.set_title("Experimental pipeline", fontsize=9, loc="left", pad=2)
    save(fig, "fig1_pipeline")

# ------------------------------------------------------------------ FIG 2
def fig2_confusion():
    fig, axes = plt.subplots(3, 2, figsize=(7.5, 5.4),
                             gridspec_kw={"hspace": 0.45, "wspace": 0.3})
    letters = iter("abcdef")
    for r, ds in enumerate(DATASETS):
        sub = res[(res["Dataset"] == ds) & (res["Modelo"] == "LSTM")]
        base = sub[sub["Cenario"] == "Original (sem balancear)"].iloc[0]
        best = best_bal(sub)
        for c, (row, tag) in enumerate([(base, "Original"), (best, "Best balanced")]):
            ax = axes[r][c]
            m = np.array([[row["TN"], row["FP"]], [row["FN"], row["TP"]]])
            im = ax.imshow(m, cmap="Blues")
            ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
            ax.set_xticklabels(["Benign", "Malware"])
            ax.set_yticklabels(["Benign", "Malware"])
            ax.set_title(f"({next(letters)}) {ds}: {tag}", fontsize=8)
            for i in range(2):
                for j in range(2):
                    ax.text(j, i, f"{int(m[i, j]):,}", ha="center", va="center",
                            fontsize=8, color="white" if m[i, j] > 1900 else "black")
            ax.tick_params(axis="both", which="both", length=0)
    fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02)
    save(fig, "fig2_confusion")

# ------------------------------------------------------------------ FIG 3
def fig3_metrics():
    cen = ["Original (sem balancear)", "SMOTETomek", "GAN+MLP", "WGAN-GP",
           "cWGAN-GP", "CTGAN"]
    modelos = ["MLP", "XGBoost", "RandomForest", "LSTM"]
    fig, axes = plt.subplots(1, 4, figsize=(8.6, 2.5),
                             gridspec_kw={"wspace": 0.28})
    vmin = res["F1-Score"].min(); vmax = 1.0
    for k, mdl in enumerate(modelos):
        piv = np.full((3, 6), np.nan)
        for i, ds in enumerate(DATASETS):
            for j, c in enumerate(cen):
                row = res[(res["Dataset"] == ds) & (res["Modelo"] == mdl)
                          & (res["Cenario"] == c)]
                if len(row):
                    piv[i, j] = row["F1-Score"].iloc[0]
        ax = axes[k]
        im = ax.imshow(piv, cmap="YlGnBu", vmin=vmin, vmax=vmax)
        ax.set_xticks(range(6)); ax.set_xticklabels(cen, rotation=60, ha="right", fontsize=6.5)
        ax.set_yticks(range(3)); ax.set_yticklabels(["Edge", "TON", "IoT-23"], fontsize=7)
        ax.set_title(mdl, fontsize=8)
        for i in range(3):
            for j in range(6):
                if not np.isnan(piv[i, j]):
                    ax.text(j, i, f"{piv[i, j]:.3f}", ha="center", va="center", fontsize=6)
    fig.suptitle("F1-score per dataset, model, and balancing strategy", fontsize=10, y=1.02)
    fig.colorbar(im, ax=axes, fraction=0.02, pad=0.02)
    save(fig, "fig3_metrics")

# ------------------------------------------------------------------ FIG 4
def fig4_fnfptp():
    cen = ["Original (sem balancear)", "SMOTETomek", "GAN+MLP", "WGAN-GP",
           "cWGAN-GP", "CTGAN"]
    modelos = ["MLP", "XGBoost", "RandomForest", "LSTM"]
    cores = [BLUE, ORANGE, GREEN, PURPLE]
    fig, axes = plt.subplots(1, 3, figsize=(8.6, 2.6), sharey=True,
                             gridspec_kw={"wspace": 0.05})
    x = np.arange(len(cen)); w = 0.2
    for a, ds in enumerate(DATASETS):
        ax = axes[a]
        for k, mdl in enumerate(modelos):
            fns = [res[(res["Dataset"] == ds) & (res["Modelo"] == mdl)
                       & (res["Cenario"] == c)]["FN"].iloc[0] for c in cen]
            ax.bar(x + (k - 1.5) * w, fns, w, label=mdl, color=cores[k])
        ax.set_xticks(x); ax.set_xticklabels(cen, rotation=60, ha="right", fontsize=6.5)
        ax.set_title(ds, fontsize=8)
        if a == 0:
            ax.set_ylabel("False negatives")
        ax.legend(frameon=False, fontsize=6, ncol=2)
    fig.suptitle("False negatives per model and balancing strategy (fixed test set)", fontsize=10, y=1.04)
    save(fig, "fig4_fnfptp")

fig1_pipeline()
fig2_confusion()
fig3_metrics()
fig4_fnfptp()
print("All figures generated.")