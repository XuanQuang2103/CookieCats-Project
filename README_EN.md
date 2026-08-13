# Cookie Cats — Mobile Game A/B Testing Project

A/B test analysis for the puzzle game **Cookie Cats** (Tactile Entertainment): evaluating the impact of **moving the progression gate from level 30 to level 40** on player retention and engagement, following the standard corporate **CRISP-DM** process.

## Business Question

> Does moving the gate 30 → 40 improve **player retention** (D1, D7) and **engagement**? → **Go / No-Go** recommendation for the Product team.

## Dataset

- **Source:** Kaggle — *Mobile Games A/B Testing: Cookie Cats* (Tactile Entertainment via DataCamp)
- **Scale:** ~90,000 users
- **Fields:**

| Field | Meaning |
|---|---|
| `userid` | Unique player ID |
| `version` | Test group: `gate_30` (control) / `gate_40` (treatment) |
| `sum_gamerounds` | Number of rounds played in the first 14 days |
| `retention_1` | Returned after 1 day (bool) |
| `retention_7` | Returned after 7 days (bool) |

> ⚠️ The data file (`data/*.csv`) is not committed to the repo. Download the original dataset from Kaggle and place it in `data/`.

## Hypotheses

- **H0₁:** Retention_D1(gate_30) = Retention_D1(gate_40)
- **H0₂:** Retention_D7(gate_30) = Retention_D7(gate_40)
- **H0₃:** Median(sum_gamerounds | gate_30) = Median(sum_gamerounds | gate_40)

Significance threshold α = 0.05 (consider a Bonferroni correction α = 0.0167 for the 3 simultaneous tests).

## Directory structure

```
.
├── data/            # Dataset (CSV — gitignored)
├── notebooks/       # Jupyter notebooks by analysis phase
├── reports/         # Exported charts & reports (PNG, ...)
├── sql/             # SQL scripts for data preparation
├── PROJECT_CONTEXT.md   # Context, objectives, scope & detailed glossary
├── requirements.txt
└── README.md
```

## Tech Stack

- **Python:** pandas, numpy, scipy.stats, matplotlib, seaborn
- **SQL:** SQL Server (localhost / SQLEXPRESS)
- **BI:** Power BI Desktop
- **Notebook:** Jupyter

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Configure the database connection via the `.env` file (see the sample `.env` — do not commit):

```
DB_SERVER=localhost\SQLEXPRESS
DB_NAME=cookie_cats
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_TRUSTED_CONNECTION=yes
```

## Roadmap (CRISP-DM)

| Phase | Content | Status |
|---|---|---|
| 1 | Business Understanding | ✅ Done |
| 2 | EDA + Data Quality (SRM check, outlier, distribution) | ✅ Done |
| 3 | Data Preparation (SQL) | ✅ Done |
| 4 | Analysis (hypothesis test, bootstrap, segment) | ✅ Done |
| 5 | Visualization | ⏭️ Dropped Power BI dashboard (static data — see DEC-13); report as replacement |
| 6 | Insights & Recommendation | ✅ Done |
| 7 | Delivery & Documentation | ✅ Done |

## Conclusion & Recommendation

> **NO-GO — keep the gate at level 30, do not roll out gate 40** (confidence > 95%).

Three pillars of evidence: (1) **D7 retention drops 0.82pp (−4.3%)**, statistically significant beyond even the Bonferroni threshold (p = 0.0016); (2) **engagement is equal** (p = 0.051, bootstrap CI contains 0) — no upside to trade for; (3) the harm concentrates in the **medium/heavy** group (core users), while the light group is virtually unchanged. Proxy business impact (ARPDAU benchmark $0.10): **~818 D7 users lost/month per 100K installs ≈ $2,454/month ≈ $29,448/year**, linear with traffic.

## Deliverables

| Type | File |
|---|---|
| SQL scripts (idempotent) | `sql/phase3_00_create_metadata.sql`, `sql/phase3_01_build_mart_ab_test_base.sql`, `sql/phase3_02_validation_queries.sql` |
| Notebooks — EDA | `notebooks/phase2_00` → `phase2_04` |
| Notebooks — Analysis | `notebooks/phase4_01_retention` · `phase4_02_Engagement` · `phase4_03_segment` · `phase4_04_business_impact` |
| Word Report — EDA / Data Prep | `reports/CookieCats_Phase2_EDA_Data_Quality_Report.docx`, `reports/CookieCats_Phase3_DataPrepare_Report.docx` |
| Word Report — Analysis | `reports/CookieCats_Phase4_Hypothesis_Testing_Report.docx` |
| Word Report — Insights & Recommendation | `reports/CookieCats_Phase6_Insights_Recommend_Report.docx` |
| Project closeout doc | `reports/CookieCats_Phase7_Closeout-Report.docx` |
| Executive 1-slide (Go/No-Go) | `reports/CookieCats_Executive_Summary.html` |
| Decision log (14 ADR) | `docs/decision_log.md` |
| Data dictionary · Preprocessing checklist | `docs/data_dictionary.md`, `docs/preprocessing_checklist.md` |

## Reproducibility

1. Create a virtualenv and `pip install -r requirements.txt` (note: versions use `>=`, not hard-pinned — re-pin if you need a fixed build).
2. Download `cookie_cats.csv` from Kaggle and place it in `data/` (the file is gitignored, not committed).
3. Load the CSV into the SQL Server table `dbo.raw_ab_test` (⚠️ there is currently no automated script for this raw-load step — do it manually via the Import Wizard or `BULK INSERT`).
4. Run the SQL in order: `phase3_00` → `phase3_01` → `phase3_02` to build `cookie_cats.mart_ab_test_base`.
5. Configure `.env` (see the sample below) then run the notebooks in phase order.

> **Cleanup note:** the notebook `phase4_02_Engagement.ipynb` capitalizes the E, deviating from the lowercase convention of the other files (minor). The raw CSV → `dbo.raw_ab_test` load step is currently done manually, with no automated script yet.

See [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) for details on scope, assumptions, stakeholder mapping and the industry-standard terminology glossary; [`docs/decision_log.md`](docs/decision_log.md) for the decision history (14 ADR).
