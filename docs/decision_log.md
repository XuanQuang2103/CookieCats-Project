# Decision Log

**Project:** Cookie Cats A/B Test Analysis
**Purpose:** Log the major decisions across the project with their rationale. This is the "history of reasoning" — reading it back 3 months later, you still understand why this approach was chosen over another.
**Format:** Architectural Decision Record (ADR), simplified.
**Owner:** Xuân Quang
**Last updated:** 2026-08-08 (Phase 7 — Delivery & Documentation)

---

## Structure of each entry

- **Status:** `Accepted` / `Superseded` / `Under review`
- **Date:** date the decision was made
- **Phase:** which phase the decision was made in
- **Context:** the situation leading to the need for a decision
- **Decision:** what was chosen
- **Rationale:** why that was chosen
- **Alternatives considered:** what else was examined
- **Tradeoffs:** what was traded away to gain what benefit
- **Consequences:** downstream consequences

---

## DEC-01 — SRM threshold p < 0.001 instead of the standard 0.05

- **Status:** Accepted
- **Date:** Phase 1 (business understanding), reconfirmed Phase 2
- **Phase:** 2

**Context:**
The SRM (Sample Ratio Mismatch) check is the first gate of an A/B test. The default α threshold for hypothesis testing is usually 0.05. Question: which α should be used for the SRM check?

Two kinds of error to weigh:
- **Type I error** (false positive): raising an SRM alarm when the ratio is actually fine → false alarm, stopping the test needlessly.
- **Type II error** (false negative): missing a real SRM (the ratio truly deviates but goes undetected) → the entire downstream analysis is invalid. This is the most fearsome error in terms of consequences.

Note the basic relationship: α = P(Type I). Increasing α → easier to reject H0 → Type I rises but Type II falls. Looking only at this relationship, to reduce Type II (the fearsome one) you would have to **increase** α, not decrease it. This is the counter-intuitive point to resolve.

**Decision:**
Use α = 0.001 (instead of 0.05) for the SRM chi-square test. Only when p < 0.001 is the SRM considered broken.

**Rationale:**
The reason for lowering α (rather than raising it) lies in the **sample size** factor that the plain "α vs error" relationship ignores — specifically, the power of the test:

- **At n = 90K, power ≈ 100% even with α = 0.001.** Power (1 − β) depends on α, effect size, and sample size. With a very large n, the test is strong enough to detect any *meaningful* SRM even with a small α. This means lowering α **hardly increases Type II** for the SRMs we worry about — the large sample size "carries" the power for us.
- **Lowering α solves the real problem at large n: Type I / alert fatigue.** At n = 90K, chi-square is so sensitive that a trivial deviation (e.g. 49.7/50.3, which nobody cares about) also yields p < 0.05. This is the issue of statistical significance vs practical significance: at large n everything is statistically significant, so you must raise the bar to filter out what is practically significant. α = 0.001 only alarms when the deviation is large enough to suspect a real structural issue.
- **Industry standard:** Microsoft, Booking.com use thresholds of 0.001 or stricter for SRM, precisely because of alert fatigue in high-throughput testing environments (thousands of tests/year).

In short: choosing α = 0.001 is **not** to reduce Type II, but to reduce Type I — and we dare do so because the large sample size already keeps Type II low for us.

**Alternatives considered:**
- α = 0.05: at n = 90K too sensitive, false positives from trivial noise constantly → alert fatigue
- α = 0.01: a middle ground but less common than 0.001 in industry SRM practice
- Raising α above 0.05: by the pure "α vs error" logic this would reduce Type II, but at large n Type II is already low, so raising α only makes Type I worse → no benefit

**Tradeoffs:**
- Trade-off: technically, α ↓ → Type II ↑. But at n = 90K this increase is negligible for a meaningful SRM (power is still ≈100%). We only lose the ability to detect a trivial SRM (e.g. 49.9/50.1) — something that does not materially impact downstream.
- Gain: a strong reduction in Type I / false alarms, avoiding needlessly stopping the test and escalating.
- **Important caveat:** this rationale depends on a large sample size. If a future project has a small n (e.g. a few hundred/thousand), power will be low, and then lowering α to 0.001 would raise Type II significantly — so reconsider, possibly keeping a higher α.

**Consequences:**
- Phase 2 SRM check passes (chi² = 6.902, p = 0.009)
- Phase 3 SRM re-check passes (chi² = 6.919, p ≈ 0.009)
- Phase 4 analysis is validly continued

---

## DEC-02 — Keep the 87 zero-round-but-retained users

- **Status:** Accepted
- **Date:** Phase 2 (SRM Check, Group 2)
- **Phase:** 2, carried to Phase 3 (POL-2)

**Context:**
The dataset contains 87 users with `sum_gamerounds = 0` (played no rounds) but `retention_1 = 1` (29 of them also have `retention_7 = 1`). Two options: (1) treat as a data anomaly, exclude; (2) accept as real behavior and keep.

**Decision:**
Keep these 87 users in the analysis. Document the working assumption: **retention metrics track app opens, not actual gameplay.**

**Rationale:**
- This is explainable behavior: user installs → opens the app → doesn't play yet → closes → opens again the next day. The app session exists, the gameplay session does not.
- Excluding these users = throwing away 87 data points of real behavior. It affects retention rate estimation.
- The working assumption "retention tracks app opens" matches how many mobile analytics platforms (Firebase, Appsflyer) track retention by default.

**Alternatives considered:**
- Exclude the 87 users: reduces sample size, throws away data without justification
- Flag them separately: adds complexity, no clear benefit

**Tradeoffs:**
- Trade-off: "retention" in this project does not mean "player retention" in the gameplay sense
- Gain: preserves sample size and data integrity

**Consequences:**
- In the final report, clearly distinguish "app retention" vs "gameplay retention"
- Any conclusion about "players returning to play" must be qualified with this caveat
- Stakeholder deliverables need a one-line disclaimer about interpretation

---

## DEC-03 — Exclude only 1 outlier user with 49,854 rounds

- **Status:** Accepted
- **Date:** Phase 3
- **Phase:** 3 (POL-3, POL-4)

**Context:**
Phase 2 Group 4 (Outlier Analysis) found 1 user with `sum_gamerounds = 49,854` — about 1000× the median. Over 14 days = 3,561 rounds/day = ~148 rounds/hour continuously 24/7. Not realistic for a human player.

**Decision:**
Exclude only this single user. Do not apply any other threshold-based filtering — all remaining users (including those with 2,000-3,000 rounds) are kept.

**Rationale:**
- The bot/emulator hypothesis is strong: 148 rounds/hour continuous cannot be human behavior
- The "smaller" outliers (e.g. 2,000-3,000 rounds) could be legitimate hardcore players — should not be thrown away
- Keep data intervention to a minimum: every filter is a source of potential bias

**Alternatives considered:**
- **Winsorize at p99:** simple, standard practice, but throws away the signal of legitimate heavy users
- **Dual-track (2 versions with/without outlier):** the most thorough but doubles the analysis complexity
- **Exclude nothing:** keep the 49,854 user, use median/non-parametric — but the chi² test and mean-based metrics would be strongly distorted

**Tradeoffs:**
- Trade-off: removing 1 record may create a small bias (reduces gate_30's n by 1 more)
- Gain: the `sum_gamerounds` distribution is no longer pulled by an extreme outlier; mean/variance metrics are more reliable

**Consequences:**
- `mart_ab_test_base` has 90,188 rows (raw 90,189 − 1)
- SRM re-check still PASSES after exclusion
- Phase 4 should still prefer non-parametric methods (Mann-Whitney U) for engagement analysis because the distribution is still right-skewed

---

## DEC-04 — Engagement bucket computed on the total population

- **Status:** Accepted
- **Date:** Phase 3
- **Phase:** 3 (POL-6, POL-7)

**Context:**
Users need to be split into 3 engagement groups (light/medium/heavy) by percentile of `sum_gamerounds`. Two approaches:
- **Approach A:** compute p33/p67 on the whole population (both groups combined) → one common threshold
- **Approach B:** compute p33/p67 separately per group → each group has its own threshold

**Decision:**
Choose Approach A — compute percentiles on the whole population after dedup + outlier removal.

**Rationale:**
- For an A/B test, the key question is "how do gate_30 and gate_40 differ". A comparison needs the **same measuring stick** between the two groups.
- Approach B makes "heavy user of gate_30" a different definition from "heavy user of gate_40" → a cross-group comparison is not meaningful.
- Approach A allows a meaningful question: "among all heavy users, what is the proportion of gate_30 vs gate_40?"

**Alternatives considered:**
- Approach B: useful when analyzing behavior internal to each group, but not the main use case
- Fixed thresholds (e.g. 10, 50, 200 rounds): easy to understand but arbitrary, not data-driven

**Tradeoffs:**
- Trade-off: if the two groups have very different distributions, a common threshold may mask insight about the distribution shift
- Gain: comparable buckets, valid cross-group analysis

**Consequences:**
- The bucket distribution may skew slightly from 33/34/33 due to discrete ties at the boundary percentile
- If Phase 4 wants to analyze the "heavy user internal to each group" angle further, buckets can be computed separately as a supplementary analysis

---

## DEC-05 — Naming convention: `dbo` for raw, `cookie_cats` for analytics

- **Status:** Accepted
- **Date:** Phase 3, Step 1
- **Phase:** 3

**Context:**
The `cookie_cats` database already has the raw table in the `dbo` schema (`dbo.raw_ab_test`). A schema layout for the downstream tables (mart, meta) needs to be decided.

**Decision:**
- Keep the raw table at `dbo.raw_ab_test`, do not move it
- Create a `cookie_cats` schema inside the `cookie_cats` database for the entire analytics layer
- Prefix: `mart_` for analysis-ready tables, `meta_` for audit tables

**Rationale:**
- A clear boundary: `dbo` = external/raw data, the `cookie_cats` schema = the analysis layer owned by the project team
- No need to touch the raw table → reduces the risk of accidental corruption
- The `mart_` / `meta_` prefix convention is inspired by dbt and modern data stack practices

**Alternatives considered:**
- Everything in `dbo`: simpler but loses the raw/analytics boundary
- Separate schemas for `mart` and `meta` (2 schemas): overkill for this scope

**Tradeoffs:**
- Trade-off: the fully qualified name is longer (`cookie_cats.mart_ab_test_base` vs `dbo.mart_ab_test_base`)
- Gain: clarity about layer boundaries, easier to grant permissions per schema later if it scales

**Consequences:**
- Every downstream query (Phase 4, Power BI, notebooks) references `cookie_cats.mart_ab_test_base`
- If backing up, the `cookie_cats` schema can be backed up separately without the raw data

---

## DEC-06 — Do not cast `retention_1` / `retention_7` to BIT

- **Status:** Accepted
- **Date:** Phase 3
- **Phase:** 3 (POL-5)

**Context:**
The raw table has `retention_1` and `retention_7` of type `BIGINT` with values 0/1. Semantically they are binary variables — casting to `BIT` would be more semantically correct and save storage.

**Decision:**
Keep the native `BIGINT`, do not cast to `BIT`.

**Rationale:**
- Power BI reads `BIT` as boolean, which sometimes causes trouble with DAX aggregation. `BIGINT` reads directly as 0/1 and `AVG()` = retention rate easily.
- pandas reads `BIGINT` as `int64` — predictable behavior; `BIT` may come out as `bool` or `int8` depending on the driver, less consistent.
- The space savings are negligible with 90K rows.

**Alternatives considered:**
- Cast to `BIT`: more semantically correct, but worse downstream tool compatibility
- Cast to `TINYINT`: a middle ground, but with no clear benefit

**Tradeoffs:**
- Trade-off: the type does not accurately reflect the semantics (a binary flag stored as BIGINT)
- Gain: downstream compatibility with Power BI, pandas, notebooks

**Consequences:**
- In `data_dictionary.md`, clearly note that the column is a binary flag with domain {0, 1} despite being of type `BIGINT`
- Downstream aggregation code: `AVG(CAST(retention_1 AS FLOAT))` to avoid integer division

---

## DEC-07 — Cross-validation between SQL and Python for statistical checks

- **Status:** Accepted (post-incident)
- **Date:** Phase 3 (arose during VAL-5 verification)
- **Phase:** 3

**Context:**
While running VAL-5 (SRM re-check), the SQL implementation of the chi-square formula returned chi² = 13.84 → FAIL, whereas the Phase 2 Python implementation on the same data gave chi² = 6.902 → PASS. After debugging, an algebra bug was found in the SQL formula — an extra factor of 2.

Root cause: when deriving the simplified formula `χ² = k × (n30 - n40)² / n` for the expected 50/50 case, the coefficient k was computed wrong. The correct value is k = 1, but it was written as k = 2.

**Decision:**
From now on, every statistical formula written in SQL for analytical checks must be cross-validated against a reference implementation (scipy/statsmodels) before the result is trusted.

**Rationale:**
- SQL has no standard unit test framework for statistical formulas
- A "simplified" formula saves compute but increases the risk of an algebra error
- The cost of a cross-check is low (~5 minutes), the benefit high (catch a silent bug)

**Alternatives considered:**
- No cross-check: faster but proven unsafe
- Use scipy in Python and drop the SQL statistical checks: loses the data quality gate in the SQL layer

**Tradeoffs:**
- Trade-off: adds 1 verification step per check
- Gain: catches bugs of this kind early

**Consequences:**
- The VAL-5 formula is fixed: `χ² = (n30 - n40)² / n`
- Preventive: downstream analytical SQL scripts (Phase 4-6 if any) must have a comparison test against Python
- Lesson embedded: user Xuân Quang spotted the discrepancy thanks to cross-checking against the Phase 2 output — this is good data science hygiene, keep this habit

---

## DEC-08 — Single-layer mart instead of dual-layer (base + analysis)

- **Status:** Accepted
- **Date:** Phase 3, Step 1
- **Phase:** 3 (POL-9)

**Context:**
Initially there was a proposal for 2 layers: `mart_ab_test_base` (full flags, no filter) + `mart_ab_test_analysis` (filtered per policy). This would allow a sensitivity analysis: "does the result change if we include/exclude the outlier?".

**Decision:**
Settle on a single layer: `cookie_cats.mart_ab_test_base` (with all policies applied).

**Rationale:**
- For the Cookie Cats scope (only 1 outlier excluded), a sensitivity analysis does not justify the overhead of 2 layers
- If sensitivity is needed, the `mart` can be temporarily rebuilt with a different policy in Phase 4 and then rolled back
- Simpler for Power BI: 1 source of truth, 1 dataset

**Alternatives considered:**
- 2-layer: more robust for sensitivity analysis, suited to an enterprise scope
- 0-layer (query raw directly each time): not repeatable, no audit trail

**Tradeoffs:**
- Trade-off: loses the ability to quickly compare "result with vs without outlier"
- Gain: simplicity, easy to maintain, downstream clarity

**Consequences:**
- If Phase 4 wants a sensitivity check of the outlier's impact, a temporary mart rebuild is needed — plan into the Phase 4 timeline if required

---

## DEC-09 — Method for the retention hypothesis test (Phase 4, Group 1)

- **Status:** Accepted
- **Date:** Phase 4
- **Phase:** 4 (Group 1)

**Context:**
A method must be fixed for testing H0₁ (D1) and H0₂ (D7) for the binary retention variable, and how to read the result at n = 90K where everything is easily statistically significant.

**Decision:**
Use the **Chi-square test of independence** (report both with/without Yates correction) as the main test, together with **Cohen's h** (effect size) and a **95% CI for the difference of proportions** (Wald), read under the **Bonferroni α = 0.0167** threshold (3 simultaneous tests). Place effect size and CI **on equal footing** with the p-value when concluding.

**Rationale:**
- Retention is binary + version is categorical → the χ² test of independence fits the nature of the data; for a 2×2 table it is equivalent to the z-test of two proportions (χ² = z²).
- At large n, the p-value is almost always small → effect size + CI must be used to separate statistical vs practical significance. Cohen's h is the standard for a difference of proportions.
- 3 simultaneous tests → Bonferroni guards against false positives; the cost of a false positive is high (a real product recommendation) so its conservatism is accepted.

**Alternatives considered:**
- 2-sample t-test: wrong assumption for a Bernoulli variable, less standard than χ².
- Report only the p-value: dangerous at large n — easy to declare "significant" for a tiny difference.
- No correction: risk of false positives when running many tests.

**Tradeoffs:**
- Trade-off: Bonferroni is conservative → may miss a truly small effect. Accepted because certainty is prioritized.
- Gain: robust conclusions, clearly distinguishing "significant" vs "worth deploying".

**Consequences:**
- Result G1: D1 does **not** reject H0₁ (p≈0.075, CI contains 0); D7 **rejects** H0₂ (p≈0.0016 < 0.0167, CI ⊂ (−∞,0)), gate_40 drops ~4.3% relative.
- Effect size (Cohen's h ≈ −0.02) is very small → tiny magnitude/user, but at large scale it is still worth money → carries over to G4.
- This method applies to every downstream proportion comparison (including segment G3).

---

## DEC-10 — Method for the engagement test (Phase 4, Group 2)

- **Status:** Accepted
- **Date:** Phase 4
- **Phase:** 4 (Group 2)

**Context:**
`sum_gamerounds` is strongly right-skewed (median ~16-17 but mean ~51 due to the long tail), so a t-test/mean-based method is unsuitable. A method must be fixed for testing H0₃ and how to obtain the CI for the median difference.

**Decision:**
Use **Mann-Whitney U** (non-parametric, suited to a skewed distribution) as the main test, effect size **rank-biserial**, and a **10,000-resample bootstrap** (seed = 42) for the 95% CI of the median difference. Read under Bonferroni α = 0.0167.

**Rationale:**
- Median + non-parametric is robust to right-skew, not dragged by tail outliers.
- Bootstrap gives a CI for the median difference without distributional assumptions.
- A fixed seed (42) ensures reproducibility.

**Alternatives considered:**
- 2-sample t-test on the mean: wrong assumption for a skewed distribution, the mean is dominated by outliers.
- Log-transform then t-test: hard to interpret for business (units of log-rounds).

**Tradeoffs:**
- Trade-off: the median is less "sensitive" than the mean to tail shifts. Accepted because engagement is typically read via the median.
- Gain: robust conclusions, a CI that does not depend on a normality assumption.

**Consequences:**
- Result G2: median 17 (gate_30) vs 16 (gate_40); Mann-Whitney p ≈ 0.0509; rank-biserial r ≈ −0.0075 (extremely small); bootstrap CI of the median diff = [−1.00; 0.00] **contains 0** → does **not** reject H0₃. The engagement of the two groups is essentially equal.
- This conclusion is the crux of the recommendation: gate_40 has no engagement upside to offset the lost D7 retention.

---

## DEC-11 — Segment analysis (HTE) by engagement bucket & note on the heavy count

- **Status:** Accepted (with open item)
- **Date:** Phase 4 (Group 3)
- **Phase:** 4 (Group 3)

**Context:**
The average D7 effect (−0.82pp) may hide heterogeneity. It needs to be checked whether the impact is uniform across light/medium/heavy (Heterogeneous Treatment Effect).

**Decision:**
Run a chi-square on D7 retention within each engagement group (using the common bucket from DEC-04), reading by **pattern** (direction + magnitude + monotonicity) rather than hard claims per cell — because each group's sample size is smaller and per-cell p-values are less stable.

**Rationale:**
- Segment insight is what the Game Designer needs most; a monotonic pattern is more valuable than an isolated p-value.
- Reading by pattern avoids over-claiming in each small-sample cell.

**Consequences:**
- Result: light +0.11pp (p=0.44) → virtually unchanged; medium −0.63pp (p=0.043); heavy −1.27pp (p=0.029). The monotonic pattern light→medium→heavy matches the mechanism: light players leave before reaching the gate; only medium/heavy players feel the comeback-habit effect.
- **Open item (needs reconciliation):** The chart `phase4_g3_segment_d7.png` shows the heavy label as 47.2% vs 46.4% (≈ −0.8pp), differing from the −1.27pp figure in the text. Too far apart to be mere rounding → suspect a difference in the heavy bucket definition between the chart and the delta computation. The direction and order are still correct and do not change the conclusion, but the notebook `phase4_03_segment_analysis` should be reconciled to fix the definitive heavy figure before external release. Xuân Quang decided to keep it as-is and noted it in Phase 7 (does not block delivery).

---

## DEC-12 — Business impact via D7 retention proxy + ARPDAU benchmark

- **Status:** Accepted
- **Date:** Phase 4 (Group 4), reconfirmed Phase 6
- **Phase:** 4 → 6

**Context:**
The dataset contains no revenue (out of scope), but the success criteria require a quantified business impact. A transparent and defensible way to convert the retention delta into money is needed.

**Decision:**
Use D7 retention as a **proxy** for stickiness/LTV. Conversion: D7 users lost/month = Installs × |ΔD7|; value per user = **LTV proxy = ARPDAU × estimated active days**. In Phase 4, leave ARPDAU as a **parameter**; in Phase 6 fix the **ARPDAU benchmark = $0.10** (casual puzzle) and LTV proxy ≈ $3.00/user (≈ 30 active days), running a sensitivity table by traffic scale.

**Rationale:**
- No real revenue → a proxy must be used; D7 retention is an industry-standard stickiness proxy.
- Leaving ARPDAU as a parameter lets the team plug in real numbers; the $0.10 benchmark only illustrates a figure for a learning case study.
- Transparent assumptions > pretending precision.

**Alternatives considered:**
- Not converting to money, reporting only % : correct but does not meet the "quantified impact" success criterion.
- A full LTV model: infeasible because only D1/D7 exist, no long-term retention curve.

**Tradeoffs:**
- Trade-off: the USD figure is illustrative, not a direct measurement — must include a clear caveat.
- Gain: non-technical stakeholders get a "feel" for the magnitude of the impact.

**Consequences:**
- Fixed figures (ARPDAU $0.10): ~818 D7 users lost/month per 100K installs ≈ $2,454/month ≈ $29,448/year, linear with traffic.
- Every deliverable must clearly state this is a benchmark-based proxy, not directly measured revenue.

---

## DEC-13 — Drop the Power BI dashboard (Phase 5), report as replacement

- **Status:** Accepted
- **Date:** Phase 7 (re-scoping Phase 5)
- **Phase:** 5 → 7

**Context:**
The original roadmap had Phase 5 building a Power BI dashboard for the Product team. However, this is an A/B test that has **already ended on static data** — the numbers will not be updated in the future.

**Decision:**
Do not build a `.pbix` dashboard. Use the Word reports (Phase 4 + Phase 6) and the executive 1-slide as the replacement visual deliverables.

**Rationale:**
- A dashboard creates value when data is refreshed periodically and needs continuous monitoring. With closed static data, a dashboard is unnecessary overhead — nobody "monitors" a finished experiment.
- A static report (embedded charts + interpretation) conveys enough insight for every stakeholder in this case study.

**Alternatives considered:**
- Build a dashboard for the sake of it: effortful, creates no real monitoring value.
- An HTML mockup dashboard: considered, but the report is already sufficient, avoiding duplication.

**Tradeoffs:**
- Trade-off: loses the interactive presentation piece; missing one "eye-catching" deliverable for a portfolio.
- Gain: focus effort on the quality of the report + recommendation.

**Consequences:**
- The final deliverables include: SQL scripts, notebooks (Phase 2, 4), Word reports (Phase 2/3/4/6), the project closeout doc, the executive 1-slide (HTML). No `.pbix`.
- If a live A/B test version (data refresh) exists later, consider building a dashboard then.

---

## Notes

- This file will continue to be updated in Phases 4-7 with new decisions (e.g. the hypothesis test threshold, the choice between parametric vs bootstrap, the business impact estimation methodology).
- When a decision is superseded, keep the old entry and mark `Status: Superseded by DEC-XX`, do not delete. The history of reasoning is as important as the conclusion.
