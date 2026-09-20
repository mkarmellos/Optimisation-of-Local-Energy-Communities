# -*- coding: utf-8 -*-
"""
Synthetic Load Generator – Residential
STL + Controlled Residual Bootstrap
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from statsmodels.tsa.seasonal import STL

# =============================== USER SETTINGS ===============================

INPUT_CSV = "Typical Energy Load -residential.csv"
TIME_COL  = None
LOAD_COL  = "Power [kW]"
DAYFIRST  = True

N_SYN = 10
SEED  = 2026

PEAK_LIMIT_REL = 0.25   # higher tolerance for residential peaks

OUT_CSV     = "synthetic_profiles_residential.csv"
OUT_METRICS = "synthetic_metrics_residential.csv"
OUT_DIR     = "outputs/residential"

# =============================== HELPERS =====================================

def read_df(path, load_col, dayfirst=True, time_col=None):
    if time_col is None:
        df = pd.read_csv(path, index_col=0, parse_dates=True, dayfirst=dayfirst)
        df.index = pd.to_datetime(df.index)#, dayfirst=dayfirst)
    else:
        df = pd.read_csv(path)
        df[time_col] = pd.to_datetime(df[time_col])#, dayfirst=dayfirst)
        df = df.sort_values(time_col).set_index(time_col)
    if load_col not in df.columns:
        raise ValueError(f"Load column {load_col} not found.")
    return df.sort_index()

def infer_samples_per_day(idx):
    try:
        delta = idx[1] - idx[0]
        return int(round(pd.Timedelta(days=1) / delta))
    except Exception:
        return 24

# =============================== SYNTHESIS ===================================

def synthesize(series, n_syn, seed):
    rng = np.random.default_rng(seed)
    spd = infer_samples_per_day(series.index)

    stl = STL(series, period=spd, robust=True)
    res = stl.fit()

    trend    = res.trend
    seasonal = res.seasonal
    resid    = res.resid

    valid = resid.notna()
    trend    = trend[valid]
    seasonal = seasonal[valid]
    resid    = resid[valid]
    idx      = series.index[valid]

    empirical_min = series.min()

    resid_pool = resid.values.copy()
    resid_pool = resid_pool[~np.isnan(resid_pool)]

    out = pd.DataFrame(index=idx)
    out["load"] = series.loc[idx]

    daily_peaks = series.groupby(series.index.floor("D")).max()

    for k in range(1, n_syn + 1):
        rng_k = np.random.default_rng(seed + 1000 * k)

        # higher building heterogeneity for residential
        amp = float(np.exp(rng_k.normal(0.0, 0.18)))

        syn_resid = rng_k.choice(resid_pool, size=len(idx), replace=True)
        syn_resid *= 0.8   # stronger residual influence

        syn = amp * (trend.values + seasonal.values) + syn_resid
        syn = pd.Series(syn, index=idx)

        syn[syn < empirical_min] = empirical_min

        for d, g in syn.groupby(syn.index.floor("D")):
            ref = daily_peaks.loc[d]
            max_p = (1 + PEAK_LIMIT_REL) * ref
            min_p = (1 - PEAK_LIMIT_REL) * ref
            p = g.max()
            if p > max_p:
                syn.loc[g.idxmax()] = max_p
            elif p < min_p:
                syn.loc[g.idxmax()] = min_p

        out[f"Synthetic_Load_{k}"] = syn

    return out

# =============================== METRICS & PLOTS =============================

def compute_metrics(original, synthetic, spd):
    dt_h = 24/spd
    diff = synthetic - original
    r = np.corrcoef(original, synthetic)[0,1] if (np.std(original) > 0 and np.std(synthetic) > 0) else 0.0
    return {
        "mean_original": float(original.mean()),
        "mean_synthetic": float(synthetic.mean()),
        "std_original": float(original.std()),
        "std_synthetic": float(synthetic.std()),
        "peak_original": float(original.max()),
        "peak_synthetic": float(synthetic.max()),
        "annual_kwh_original": float(original.sum()) * dt_h,
        "annual_kwh_synthetic": float(synthetic.sum()) * dt_h,
        "MAE": float(np.mean(np.abs(diff))),
        "RMSE": float(np.sqrt(np.mean(diff**2))),
        "Pearson_r": float(r)
    }

def make_metrics_table(df):
    orig = df["load"]
    spd  = infer_samples_per_day(df.index)
    rows = [{"series":"original", **compute_metrics(orig, orig, spd)}]
    for c in [c for c in df.columns if c.startswith("Synthetic_Load_")]:
        rows.append({"series": c, **compute_metrics(orig, df[c], spd)})
    return pd.DataFrame(rows)

PALETTE = [
    "#1f77b4",
    "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]
LINEWIDTH = 1.0

LEGEND_NCOL_ORIGINAL = 1
LEGEND_NCOL_OVERLAY  = round(N_SYN/2)+1
LEGEND_NCOL_PAIR     = 2

def _create_figure_with_legend_row(figsize=(10, 6.0), legend_ratio=0.22):
    fig = plt.figure(figsize=figsize, constrained_layout=False)
    gs  = GridSpec(nrows=2, ncols=1, height_ratios=[1.0 - legend_ratio, legend_ratio], figure=fig)
    ax     = fig.add_subplot(gs[0])
    ax_leg = fig.add_subplot(gs[1])
    ax_leg.axis("off")
    return fig, ax, ax_leg

def plot_original(df_out: pd.DataFrame, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    fig, ax, ax_leg = _create_figure_with_legend_row(figsize=(12, 4.8), legend_ratio=0.18)
    df_out["load"].plot(ax=ax, color=PALETTE[0], linewidth=LINEWIDTH,
                        label="Sample Residential Electricity Load")
    ax.set_xlabel("Timestep", labelpad=8)
    ax.set_ylabel("Electricity Demand [kW]")
    ax.grid(alpha=0.3)
    handles, labels = ax.get_legend_handles_labels()
    ax_leg.legend(handles, labels,
                  loc="lower center", bbox_to_anchor=(0.5, 0.0),
                  ncol=LEGEND_NCOL_ORIGINAL, frameon=True, borderaxespad=0.0)
    fig.savefig(os.path.join(outdir, "original.png"), dpi=600, bbox_inches="tight")
    plt.close(fig)

def plot_synthetics_overlay(df_out: pd.DataFrame, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    syn_cols = [c for c in df_out.columns if c.startswith("Synthetic_Load_")]
    fig, ax, ax_leg = _create_figure_with_legend_row(figsize=(12, 5.2), legend_ratio=0.24)
    for i, c in enumerate(syn_cols, start=1):
        color = PALETTE[i % len(PALETTE)]
        df_out[c].plot(ax=ax, color=color, linewidth=LINEWIDTH, label=c)
    df_out["load"].plot(ax=ax, color=PALETTE[0], linewidth=LINEWIDTH,
                        label="Sample Residential Electricity Load")
    ax.set_xlabel("Timestep", labelpad=8)
    ax.set_ylabel("Electricity Demand [kW]")
    ax.grid(alpha=0.3)
    handles, labels = ax.get_legend_handles_labels()
    ax_leg.legend(handles, labels,
                  loc="lower center", bbox_to_anchor=(0.5, 0.0),
                  ncol=LEGEND_NCOL_OVERLAY, frameon=True, borderaxespad=0.0)
    fig.savefig(os.path.join(outdir, "synthetics_overlay.png"), dpi=600, bbox_inches="tight")
    plt.close(fig)

def plot_each_vs_original(df_out: pd.DataFrame, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    syn_cols = [c for c in df_out.columns if c.startswith("Synthetic_Load_")]
    for i, c in enumerate(syn_cols, start=1):
        fig, ax, ax_leg = _create_figure_with_legend_row(figsize=(12, 4.8), legend_ratio=0.18)
        df_out["load"].plot(ax=ax, color=PALETTE[0], linewidth=LINEWIDTH,
                            label="Sample Residential Electricity Load")
        color = PALETTE[i % len(PALETTE)]
        df_out[c].plot(ax=ax, color=color, linewidth=LINEWIDTH, label=c)
        ax.set_xlabel("Timestep", labelpad=8)
        ax.set_ylabel("Electricity Demand [kW]")
        ax.grid(alpha=0.3)
        handles, labels = ax.get_legend_handles_labels()
        ax_leg.legend(handles, labels,
                      loc="lower center", bbox_to_anchor=(0.5, 0.0),
                      ncol=LEGEND_NCOL_PAIR, frameon=True, borderaxespad=0.0)
        fig.savefig(os.path.join(outdir, f"{c}_vs_original.png"), dpi=600, bbox_inches="tight")
        plt.close(fig)

# =============================== MAIN ========================================

if __name__ == "__main__":
    df = read_df(INPUT_CSV, LOAD_COL, DAYFIRST, TIME_COL)
    series = df[LOAD_COL].astype(float)

    df_out = synthesize(series, N_SYN, SEED)
    df_out.to_csv(OUT_CSV)
    print(f"[OK] Saved → {OUT_CSV}")

    metrics = make_metrics_table(df_out)
    metrics.to_csv(OUT_METRICS, index=False)
    print(f"[OK] Saved → {OUT_METRICS}")

    os.makedirs(OUT_DIR, exist_ok=True)
    plot_original(df_out, OUT_DIR)
    plot_synthetics_overlay(df_out, OUT_DIR)
    plot_each_vs_original(df_out, OUT_DIR)
    print(f"[OK] Saved plots in → {OUT_DIR}")

