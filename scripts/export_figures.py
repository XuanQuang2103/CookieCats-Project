"""Export the three headline Phase-4 figures used in README.md.

Reads the analysis mart (SQL Server if configured, CSV fallback with the same
mart policy as sql/phase3_01_build_mart_ab_test_base.sql) and writes:

    reports/figures/fig1_retention_by_group.png
    reports/figures/fig2_segment_d7.png
    reports/figures/fig3_bootstrap_median_ci.png

Usage:
    python scripts/export_figures.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from scipy import stats

RANDOM_STATE = 42
ALPHA = 0.05
N_TESTS = 3
ALPHA_BONF = ALPHA / N_TESTS
N_BOOT = 5000
OUTLIER_ROUNDS = 49854  # single impossible value removed in Phase 2 (see DEC-03)

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "reports" / "figures"
CSV_PATH = ROOT / "data" / "cookie_cats.csv"

COLORS = {"gate_30": "#4C72B0", "gate_40": "#DD8452"}


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_from_sql() -> pd.DataFrame:
    import os

    import pyodbc
    from dotenv import load_dotenv

    load_dotenv()
    conn = pyodbc.connect(
        f"DRIVER={{{os.getenv('DB_DRIVER')}}};"
        f"SERVER={os.getenv('DB_SERVER')};DATABASE={os.getenv('DB_NAME')};"
        f"Trusted_Connection={os.getenv('DB_TRUSTED_CONNECTION', 'yes')};"
    )
    query = (
        "SELECT userid, version, sum_gamerounds, retention_1, retention_7, "
        "engagement_bucket FROM cookie_cats.mart_ab_test_base"
    )
    return pd.read_sql(query, conn)


def load_from_csv() -> pd.DataFrame:
    raw = pd.read_csv(CSV_PATH)
    mart = (
        raw.groupby("userid")
        .agg(
            version=("version", "max"),
            sum_gamerounds=("sum_gamerounds", "max"),
            retention_1=("retention_1", "max"),
            retention_7=("retention_7", "max"),
        )
        .reset_index()
    )
    mart = mart[mart["sum_gamerounds"] != OUTLIER_ROUNDS].copy()
    mart["retention_1"] = mart["retention_1"].astype(int)
    mart["retention_7"] = mart["retention_7"].astype(int)
    # engagement_bucket: population tertiles p33 / p67 (Phase 3 policy)
    q33, q67 = mart["sum_gamerounds"].quantile([0.33, 0.67])
    mart["engagement_bucket"] = np.where(
        mart["sum_gamerounds"] <= q33,
        "light",
        np.where(mart["sum_gamerounds"] <= q67, "medium", "heavy"),
    )
    return mart


def load_mart() -> tuple[pd.DataFrame, str]:
    try:
        return load_from_sql(), "SQL Server (cookie_cats.mart_ab_test_base)"
    except Exception:
        return load_from_csv(), "CSV fallback (mart policy replicated in pandas)"


# --------------------------------------------------------------------------- #
# Figures
# --------------------------------------------------------------------------- #
def analyze_retention(df: pd.DataFrame, metric: str, n30: int, n40: int) -> dict:
    ct = pd.crosstab(df["version"], df[metric])
    r30 = df.loc[df.version == "gate_30", metric].mean()
    r40 = df.loc[df.version == "gate_40", metric].mean()
    chi2_y, p_y, _, _ = stats.chi2_contingency(ct, correction=True)
    diff = r40 - r30
    se = np.sqrt(r30 * (1 - r30) / n30 + r40 * (1 - r40) / n40)
    return dict(
        metric=metric,
        rate_30=r30,
        rate_40=r40,
        diff=diff,
        rel_lift=diff / r30 * 100,
        p_yates=p_y,
        ci=(diff - 1.96 * se, diff + 1.96 * se),
    )


def sig_label(p: float) -> str:
    if p < ALPHA_BONF:
        return f"p={p:.4f} — significant (Bonferroni)"
    if p < ALPHA:
        return f"p={p:.4f} — significant at 0.05 only"
    return f"p={p:.4f} — not significant"


def fig1_retention_by_group(mart: pd.DataFrame, n30: int, n40: int) -> None:
    res_d1 = analyze_retention(mart, "retention_1", n30, n40)
    res_d7 = analyze_retention(mart, "retention_7", n30, n40)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, res, title in zip(axes, (res_d1, res_d7), ("Day-1 retention", "Day-7 retention")):
        groups = ["gate_30", "gate_40"]
        rates = [res["rate_30"] * 100, res["rate_40"] * 100]
        errs = [
            1.96 * np.sqrt(p / 100 * (1 - p / 100) / nn) * 100
            for p, nn in zip(rates, (n30, n40))
        ]
        bars = ax.bar(
            groups,
            rates,
            yerr=errs,
            capsize=8,
            color=[COLORS[g] for g in groups],
            edgecolor="black",
            linewidth=0.6,
            error_kw=dict(ecolor="#333", lw=1.4),
        )
        for bar, value in zip(bars, rates):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + max(errs) * 1.3,
                f"{value:.2f}%",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
            )
        ax.set_title(
            f"{title}\n{res['diff'] * 100:+.2f}pp ({res['rel_lift']:+.1f}%) · {sig_label(res['p_yates'])}",
            fontsize=11,
            fontweight="bold",
        )
        ax.set_ylabel("Retention rate (%)")
        ax.set_ylim(0, max(rates) * 1.28)
        ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.0f%%"))
        ax.grid(False)

    fig.suptitle(
        "Cookie Cats — retention: gate_30 (control) vs gate_40 (treatment), error bars = 95% CI",
        fontsize=12,
        fontweight="bold",
        y=1.04,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_retention_by_group.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out.relative_to(ROOT)}")


def fig2_segment_d7(mart: pd.DataFrame) -> None:
    order = ["light", "medium", "heavy"]
    piv_rate = (
        mart.pivot_table(
            index="engagement_bucket", columns="version", values="retention_7", aggfunc="mean"
        ).reindex(order)
        * 100
    )
    piv_n = mart.pivot_table(
        index="engagement_bucket", columns="version", values="retention_7", aggfunc="count"
    ).reindex(order)

    def err(bucket: str, version: str) -> float:
        p = piv_rate.loc[bucket, version] / 100
        return 1.96 * np.sqrt(p * (1 - p) / piv_n.loc[bucket, version]) * 100

    fig, ax = plt.subplots(figsize=(9, 4.8))
    x = np.arange(len(order))
    width = 0.38
    b1 = ax.bar(
        x - width / 2,
        piv_rate["gate_30"],
        width,
        yerr=[err(b, "gate_30") for b in order],
        capsize=6,
        label="gate_30 (control)",
        color=COLORS["gate_30"],
        edgecolor="black",
        linewidth=0.6,
        error_kw=dict(ecolor="#333", lw=1.4),
    )
    b2 = ax.bar(
        x + width / 2,
        piv_rate["gate_40"],
        width,
        yerr=[err(b, "gate_40") for b in order],
        capsize=6,
        label="gate_40 (treatment)",
        color=COLORS["gate_40"],
        edgecolor="black",
        linewidth=0.6,
        error_kw=dict(ecolor="#333", lw=1.4),
    )
    for bars in (b1, b2):
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1.2,
                f"{bar.get_height():.1f}%",
                ha="center",
                va="bottom",
                fontsize=9,
            )
    ax.set_ylim(0, float(piv_rate.to_numpy().max()) * 1.2)
    deltas = [
        piv_rate.loc[b, "gate_40"] - piv_rate.loc[b, "gate_30"] for b in order
    ]
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{b.capitalize()}\n({d:+.2f}pp)" for b, d in zip(order, deltas)]
    )
    ax.set_ylabel("Day-7 retention (%)")
    ax.set_xlabel("Engagement segment (population tertiles of rounds played)")
    ax.set_title(
        "Day-7 retention by engagement segment — the loss sits in medium/heavy players",
        fontsize=12,
        fontweight="bold",
    )
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.0f%%"))
    ax.legend()
    ax.grid(False)
    fig.tight_layout()
    out = FIG_DIR / "fig2_segment_d7.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out.relative_to(ROOT)}")


def fig3_bootstrap_median_ci(mart: pd.DataFrame) -> None:
    rng = np.random.default_rng(RANDOM_STATE)
    a = mart.loc[mart.version == "gate_30", "sum_gamerounds"].to_numpy()
    b = mart.loc[mart.version == "gate_40", "sum_gamerounds"].to_numpy()
    _, p_mwu = stats.mannwhitneyu(a, b, alternative="two-sided")

    diffs = np.empty(N_BOOT)
    for i in range(N_BOOT):
        diffs[i] = np.median(rng.choice(b, b.size, replace=True)) - np.median(
            rng.choice(a, a.size, replace=True)
        )
    ci_lo, ci_hi = np.percentile(diffs, [2.5, 97.5])

    # the median of a discrete count metric is itself discrete, so plot the
    # exact resample frequencies rather than a histogram with empty bins
    values, counts = np.unique(diffs, return_counts=True)
    shares = counts / N_BOOT * 100

    fig, ax = plt.subplots(figsize=(9, 4.8))
    bars = ax.bar(values, shares, width=0.35, color="#55A868", edgecolor="black", linewidth=0.6)
    for bar, share, count in zip(bars, shares, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            share + 1.5,
            f"{share:.1f}%\n({count:,} resamples)",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax.axvline(0, color="#C44E52", ls="--", lw=1.6, label="no difference")
    ax.axvline(ci_lo, color="#333", ls=":", lw=1.4)
    ax.axvline(ci_hi, color="#333", ls=":", lw=1.4, label=f"95% CI [{ci_lo:.0f}, {ci_hi:.0f}] rounds")
    ax.set_xticks(values)
    ax.set_ylim(0, max(shares) * 1.3)
    ax.set_xlim(min(values) - 0.6, max(values) + 0.6)
    ax.set_xlabel("median(gate_40) − median(gate_30), rounds played in first 14 days")
    ax.set_ylabel(f"Share of bootstrap resamples (n = {N_BOOT:,})")
    ax.set_title(
        "Engagement: bootstrap distribution of the median difference\n"
        f"CI contains 0 · Mann-Whitney U {sig_label(p_mwu)} → no engagement upside",
        fontsize=12,
        fontweight="bold",
    )
    ax.legend()
    ax.grid(False)
    fig.tight_layout()
    out = FIG_DIR / "fig3_bootstrap_median_ci.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out.relative_to(ROOT)}")


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    mart, source = load_mart()
    print(f"Source: {source}")
    print(f"Rows: {len(mart):,}")
    assert len(mart) == 90188, "Row count differs from 90,188 — check the mart policy."

    n30 = int((mart["version"] == "gate_30").sum())
    n40 = int((mart["version"] == "gate_40").sum())

    fig1_retention_by_group(mart, n30, n40)
    fig2_segment_d7(mart)
    fig3_bootstrap_median_ci(mart)


if __name__ == "__main__":
    main()
