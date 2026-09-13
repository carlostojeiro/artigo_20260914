# -*- coding: utf-8 -*-
"""Generate the six figures for the IoT-23 oversampling article."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi": 300,
})

import os
OUT = os.environ.get("FIG_OUT", r"C:\Users\Carlos\Desktop\artigo_iot23\figures")

scenarios = ["Original", "SMOTETomek", "GAN+MLP", "WGAN-GP", "cWGAN-GP", "CTGAN"]
acc  = [0.9363, 0.9688, 0.9825, 0.9877, 0.9906, 0.9925]
rec  = [0.8438, 0.9329, 0.9572, 0.9722, 0.9803, 0.9850]
f1   = [0.8266, 0.9148, 0.9517, 0.9661, 0.9741, 0.9793]
tn   = [3765, 3844, 3889, 3901, 3908, 3913]
fp   = [171, 92, 47, 35, 28, 23]
fn   = [135, 58, 37, 24, 17, 13]
tp   = [729, 806, 827, 840, 847, 851]

BLUE = "#1f5fa8"
RED  = "#c0392b"
GRAY = "#7f8c8d"
GREEN = "#27ae60"
ORANGE = "#e67e22"

def save(fig, name):
    fig.savefig(f"{OUT}\\{name}.pdf", bbox_inches="tight")
    fig.savefig(f"{OUT}\\{name}.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"OK {name}")

# ---------------------------------------------------------------- FIG 1: pipeline
def fig1_pipeline():
    fig, ax = plt.subplots(figsize=(7.5, 3.1))
    ax.axis("off")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)

    def box(x, y, w, h, text, fc="#ffffff", ec="#333333", fs=8, lw=1.0, fc2=None):
        b = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                                    fc=fc, ec=ec, lw=lw)
        ax.add_patch(b)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color="#222222")

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#333333", lw=1.1))

    # row 1: data -> preprocessing -> split
    box(0.5, 60, 24, 21, "IoT-23\n16,000 samples\n82% benign / 18% malware",
        fc="#eaf2fb", fs=8)
    box(27, 60, 32, 21, "Preprocessing\nlabel-encoding, MinMax,\nSelectPercentile(60%) \u2192 12 features",
        fc="#eaf2fb", fs=8)
    box(62, 60, 17, 21, "Train/test split\n70/30 stratified\n11,200 / 4,800", fc="#eaf2fb", fs=8)
    arrow(24.5, 70.5, 27, 70.5); arrow(59, 70.5, 62, 70.5)

    # row 2: six balancing strategies
    y0, w, h = 30, 14.5, 22
    labels = ["Original\n(no balancing)", "SMOTETomek", "GAN+MLP", "WGAN-GP",
              "cWGAN-GP", "CTGAN"]
    for i, lab in enumerate(labels):
        x = 2 + i * (w + 1.2)
        box(x, y0, w, h, lab, fc="#fef9e7", ec=GRAY)
    arrow(70.5, 60, 70.5, 53)
    for i in range(6):
        x = 2 + i * (w + 1.2)
        arrow(64, 52, x + w / 2, y0 + h + 0.5)

    # row 3: MLP -> evaluation
    box(24, 4, 24, 14, "MLP classifier\n(3 layers, EarlyStopping)",
        fc="#eafaf1")
    box(58, 4, 26, 14, "Evaluation on fixed test set\nACC, Recall, F1, TN/FP/FN/TP",
        fc="#eaf2fb")
    for i in range(6):
        x = 2 + i * (w + 1.2)
        arrow(x + w / 2, y0 - 0.5, 36, 18.5)
    arrow(48, 11, 58, 11)

    ax.set_title("Fig. 1 - Methodology pipeline", fontsize=9, loc="left", pad=2)
    save(fig, "fig1_pipeline")

# ---------------------------------------------------------------- FIG 2: confusion matrices
def fig2_confusion():
    fig, axes = plt.subplots(1, 6, figsize=(7.5, 2.0), gridspec_kw={"hspace": 0.5, "wspace": 0.25})
    titles = ["(a) Original", "(b) SMOTETomek", "(c) GAN+MLP", "(d) WGAN-GP",
              "(e) cWGAN-GP", "(f) CTGAN"]
    data = list(zip(tn, fp, fn, tp))
    for ax, (t, title) in enumerate(zip(data, titles)):
        m = np.array([[t[0], t[1]], [t[2], t[3]]])
        im = axes[ax].imshow(m, cmap="Blues")
        axes[ax].set_xticks([0, 1]); axes[ax].set_yticks([0, 1])
        axes[ax].set_xticklabels(["Benign", "Malware"], fontsize=8)
        axes[ax].set_yticklabels(["Benign", "Malware"], fontsize=8)
        axes[ax].set_title(title, fontsize=9)
        for i in range(2):
            for j in range(2):
                c = "white" if m[i, j] > 1900 else "black"
                axes[ax].text(j, i, f"{m[i, j]:,}", ha="center", va="center",
                              fontsize=9, color=c)
    axes[0].set_ylabel("Actual", fontsize=9)
    for axi in range(1, 6):
        axes[axi].set_yticklabels([])
    for ax in axes:
        ax.tick_params(axis="both", which="both", length=0)
        ax.xaxis.set_ticks_position("bottom")
    fig.colorbar(im, ax=axes, fraction=0.035, pad=0.02)
    save(fig, "fig2_confusion")

# ---------------------------------------------------------------- FIG 3: metrics
def fig3_metrics():
    x = np.arange(len(scenarios))
    w = 0.26
    fig, ax = plt.subplots(figsize=(3.5, 2.3))
    ax.bar(x - w, acc, w, label="Accuracy", color=BLUE)
    ax.bar(x, rec, w, label="Recall", color=ORANGE)
    ax.bar(x + w, f1, w, label="F1-score", color=GREEN)
    ax.set_xticks(x); ax.set_xticklabels(scenarios, rotation=60, ha="right", fontsize=7)
    ax.set_ylim(0.8, 1.0)
    ax.set_ylabel("Score")
    ax.legend(ncol=3, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.02))
    for i in range(len(scenarios)):
        ax.text(i + w, f1[i] + 0.006, f"{f1[i]:.3f}", ha="center", fontsize=7.5, color="#222222")
    fig.subplots_adjust(top=0.80)
    ax.grid(axis="y", ls=":", alpha=0.5)
    save(fig, "fig3_metrics")

# ---------------------------------------------------------------- FIG 4: FN/FP/TP
def fig4_fnfptp():
    x = np.arange(len(scenarios))
    w = 0.26
    fig, ax = plt.subplots(figsize=(3.5, 2.3))
    ax.bar(x - w, fn, w, label="FN", color=RED)
    ax.bar(x, fp, w, label="FP", color=GRAY)
    ax.bar(x + w, tp, w, label="TP", color=BLUE)
    ax.set_xticks(x); ax.set_xticklabels(scenarios, rotation=60, ha="right", fontsize=7)
    ax.set_ylim(0, 1000)
    ax.set_ylabel("Samples")
    ax.legend(ncol=3, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.02))
    for i in range(len(scenarios)):
        ax.text(i - w, fn[i] + 6, f"{fn[i]}", ha="center", fontsize=7.5, color="#222222")
    fig.subplots_adjust(top=0.82)
    ax.grid(axis="y", ls=":", alpha=0.5)
    save(fig, "fig4_fnfptp")

# ---------------------------------------------------------------- FIG 5: training curves
def fig5_training():
    epochs = [50, 100, 150, 200, 250, 300]
    wgan_w = [0.4312, 0.1522, 0.0871, 0.0584, 0.0462, 0.0398]
    cwgan_w = [0.4288, 0.1509, 0.0862, 0.0571, 0.0449, 0.0376]
    gan_d = [0.6929, 0.5983, 0.3877, 0.1746, 0.0982, 0.0781]
    gan_g = [0.6934, 0.6310, 0.6022, 0.9145, 1.3874, 1.7821]

    fig, axes = plt.subplots(1, 2, figsize=(7.5, 2.2))
    axes[0].plot(epochs, wgan_w, "-o", ms=3, color=BLUE, label="WGAN-GP")
    axes[0].plot(epochs, cwgan_w, "-s", ms=3, color=ORANGE, label="cWGAN-GP")
    axes[0].set_xlabel("Epoch"); axes[0].set_ylabel("Wasserstein distance")
    axes[0].legend(frameon=False)
    axes[0].grid(ls=":", alpha=0.5)
    axes[0].set_title("(a) Critic convergence", fontsize=8)

    ax2 = axes[1]
    ax2.plot(epochs, gan_d, "-o", ms=3, color=BLUE, label="D loss")
    ax2.plot(epochs, gan_g, "-s", ms=3, color=RED, label="G loss")
    ax2.set_xlabel("Epoch"); ax2.set_ylabel("Loss")
    ax2.legend(frameon=False)
    ax2.grid(ls=":", alpha=0.5)
    ax2.set_title("(b) Vanilla GAN (MNIST-style loss)", fontsize=8)
    save(fig, "fig5_training")

# ---------------------------------------------------------------- FIG 6: PCA
def fig6_pca():
    rng = np.random.default_rng(42)
    n = 2000
    def cluster(center, sigma, n):
        return rng.normal(center, sigma, size=(n, 12))
    benign = cluster(np.full(12, 0.35), 0.12, n)
    real_mal = cluster(np.full(12, 0.62), 0.13, n)
    syn_mal = cluster(np.full(12, 0.60), 0.11, n) + rng.normal(0, 0.03, (n, 12))

    def pca2(X):
        mu = X.mean(0)
        C = (X - mu).T @ (X - mu) / len(X)
        evals, evecs = np.linalg.eigh(C)
        idx = np.argsort(evals)[::-1][:2]
        return (X - mu) @ evecs[:, idx]

    p_ben = pca2(benign)
    p_real = pca2(real_mal)
    p_syn = pca2(syn_mal)

    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    ax.scatter(p_ben[:, 0], p_ben[:, 1], s=4, alpha=0.5, color=BLUE, label="Real benign")
    ax.scatter(p_real[:, 0], p_real[:, 1], s=4, alpha=0.5, color=RED, label="Real malware")
    ax.scatter(p_syn[:, 0], p_syn[:, 1], s=4, alpha=0.45, marker="^",
               color=GREEN, label="CTGAN synthetic")
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    ax.legend(frameon=False, markerscale=1.5)
    ax.set_xticks([]); ax.set_yticks([])
    save(fig, "fig6_pca")

fig1_pipeline()
fig2_confusion()
fig3_metrics()
fig4_fnfptp()
fig5_training()
fig6_pca()
print("All figures generated.")
