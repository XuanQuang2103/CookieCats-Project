# PROJECT CONTEXT — Cookie Cats A/B Test Analysis

These are the project instructions for Claude. Every conversation in this Project uses the context below.

## 1. Background & rationale for the analysis

**Cookie Cats** is a mobile puzzle game (match-3) by Tactile Entertainment. The dataset captures a real A/B test:
- **gate_30 (control):** Gate blocking at level 30
- **gate_40 (treatment):** Gate moved to level 40

**Core business question:** Does moving the gate improve player retention and engagement?

**Why it matters in F2P games:**
- D1/D7 retention directly determines LTV
- The gate is the main mechanic for creating controlled friction, pushing monetization, and triggering the viral loop (inviting friends)
- Moving the gate = a trade-off between early monetization and long-term retention

---

## 2. Objectives

**Primary:** Assess the impact of moving the gate 30→40 on D1 and D7 retention with clear statistical significance → a Go/No-Go recommendation for the Product team.

**Secondary:**
- Understand the distribution of player behavior, detect segments
- Identify sub-populations affected differently (heavy vs casual users)
- Build baseline metrics for future A/B tests

**Final deliverables:**
- A Word/PDF report for non-technical stakeholders
- Reusable Python notebooks + SQL scripts

---

## 3. Formal hypotheses

- **H0₁:** Retention_D1(gate_30) = Retention_D1(gate_40)
- **H0₂:** Retention_D7(gate_30) = Retention_D7(gate_40)
- **H0₃:** Median(sum_gamerounds | gate_30) = Median(sum_gamerounds | gate_40)

**Directional expectation:** Gate_40 may increase short-term engagement (playing longer before being blocked) but may reduce long-term retention (an earlier gate builds a better comeback habit).

**Significance threshold:** α = 0.05. With 3 simultaneous tests, consider a Bonferroni correction (α_adjusted = 0.0167).

---

## 4. Stakeholder Mapping

| Stakeholder | What they care about | Suitable format |
|---|---|---|
| Product Manager | Deploy or not, ETA, risk | Dashboard + 1-page summary |
| Game Designer | Impact on player experience, segments | Deep-dive report with charts |
| Marketing Lead | Effect on LTV, CAC budget | KPI cards + business impact estimate |
| CEO / Leadership | Conclusion, money impact | Executive summary 1 slide |

---

## 5. Success Criteria (for the project, not for the A/B test)

The project succeeds when:
- There is a clear Go/No-Go recommendation with confidence >95%
- The business impact estimate is quantified (e.g. "D7 retention drops 0.8% → LTV drops ~2.4% → monthly revenue drops ~X USD")
- The data quality checklist passes fully (including the SRM check)
- The deliverables (report, dashboard, notebook) are completed

---

## 6. Scope

**IN scope:**
- Retention D1, D7
- Engagement (sum_gamerounds)
- A/B test analysis with statistical + bootstrap methods
- Segment analysis by engagement bucket

**OUT of scope:**
- Monetization (the dataset has no revenue data)
- Retention D14+ (the dataset only covers 14 days)
- Cohorts by device / geo / acquisition channel (no data)
- Session-level pattern analysis (no timestamps)

---

## 7. Assumptions & Limitations

- Random assignment between the two groups is valid → **will be verified via the SRM check in Phase 2**
- Data only covers the first 14 days → no long-term impact can be concluded
- No info on device/country/channel → cannot segment along those dimensions
- No timestamps → cannot analyze session/DAU patterns
- Retention D1/D7 are binary variables (0/1), not "number of days returned"

---

## 8. Risks

- **Data risk:** Outlier user with 49,854 rounds in 14 days — very likely a bot/emulator, needs a handling decision
- **Statistical risk:** Multiple testing (3 metrics) → needs correction
- **Business risk:** A recommendation based on 14 days may be wrong against a 3-6 month reality
- **Sample risk:** If the SRM fails → the entire A/B test is invalid and must be escalated

---

## 9. Timeline

| Phase | Content | Deadline |
|---|---|---|
| Phase 1 | Business Understanding | Done |
| Phase 2 | EDA + Data Quality | Done |
| Phase 3 | Data Preparation (SQL) | Done |
| Phase 4 | Analysis (hypothesis test, bootstrap, segment) | Done |
| Phase 5 | Visualization (Python) | Done |
| Phase 6 | Insights & Recommendation | Done |
| Phase 7 | Delivery & Documentation | Done |

Total: ~5 days.

---

## 10. Data Source

- **Source:** Kaggle dataset "Mobile Games A/B Testing - Cookie Cats"
- **Origin:** Public dataset from Tactile Entertainment via DataCamp
- **Fields:** `userid` (unique), `version` (gate_30/gate_40), `sum_gamerounds` (rounds in 14 days), `retention_1` (bool), `retention_7` (bool)
- **Size:** ~90,000 users
- **Version control:** The file hash will be recorded in Phase 2 to avoid confusion with other mirrors

---

## 11. Tech Stack

- **SQL:** SQL Server (user decides in Phase 2)
- **Python:** pandas, numpy, scipy.stats, matplotlib, seaborn
- **BI:** Power BI Desktop
- **Notebook:** Jupyter / Colab
- **Version control:** Git

---

## 12. Glossary — Industry-standard terminology

### Retention Metrics
- **Retention D_n:** Percentage of users who return on day n after install. `= Users_return_day_n / Users_install`
- **D1 Retention:** Day-1 retention (first impression). Puzzle benchmark: 35-45%
- **D7 Retention:** Day-7 retention (true stickiness). Puzzle benchmark: 10-20%
- **D30 Retention:** Proxy for long-term engagement, used to estimate LTV
- **Churn Rate:** `= 1 - Retention`

### Monetization Metrics
- **ARPU:** Revenue / Total Users (including free users)
- **ARPPU:** Revenue / Paying Users only
- **LTV (Lifetime Value):** The estimated total revenue a user generates over their entire playing lifetime. Formula: `LTV = ARPDAU × Σ(Retention_D_n)`. **Golden rule: LTV > CAC × 3**
- **CAC:** Acquisition cost per user (usually via ads)
- **Payer Conversion:** % of users converting from free to paying. Puzzle: 1-3%

### Engagement Metrics
- **DAU / MAU:** Daily / Monthly Active Users
- **Stickiness:** `DAU / MAU`. Good puzzle: 15-25%. Hardcore game: 40-50%
- **Session Length:** Average time per session
- **Game Rounds:** Number of rounds played. In the dataset it is `sum_gamerounds`

### A/B Testing
- **Control vs Treatment:** Baseline group vs the group receiving the change
- **H0 / H1:** Null hypothesis (no difference) vs Alternative (there is a difference)
- **P-value:** Probability of seeing this result (or a more extreme one) if H0 is true. Threshold: p<0.05
- **Statistical Significance:** A difference not due to chance
- **Practical Significance:** A difference large enough to be worth deploying
- **SRM (Sample Ratio Mismatch):** The user ratio of the two groups deviates greatly from the design → red flag, test invalid
- **Confidence Interval:** The confidence range of an estimate
- **Bootstrap Resampling:** Resample the dataset 10,000+ times to estimate the distribution when data is not normal

### Game Design
- **Gate (Progression Gate):** A mechanic that blocks progress at one point, forcing the user to wait/invite/pay
- **Hard Gate vs Soft Gate:** Mandatory vs incentivized-if-you-wait
- **Onboarding:** The first-minutes experience, which determines D1
- **Hook Point / Aha Moment:** The moment the user "gets" why the game is fun. Puzzle: level 3-5
- **Difficulty Curve:** The curve of difficulty across levels

### Statistical Concepts
- **Skewness:** The skew of a distribution. Sum_gamerounds will be right-skewed
- **Outlier:** An abnormal value (e.g. the user with 49K rounds)
- **Chi-square Test:** For categorical variables (retention 0/1)
- **Mann-Whitney U:** Non-parametric test when data is not normal (for sum_gamerounds)
- **Winsorize:** Cap outliers at a certain percentile (e.g. p99)
