# Data Dictionary — `cookie_cats.mart_ab_test_base`

**Project:** Cookie Cats A/B Test Analysis
**Table:** `cookie_cats.mart_ab_test_base`
**Layer:** Analytics mart (analysis-ready, Phase 4 downstream)
**Row count:** 90,188
**Row grain:** 1 row = 1 unique user
**Primary key:** `userid`
**Source table:** `dbo.raw_ab_test` (90,189 rows)
**Snapshot date:** 2026-08-07
**Owner:** Xuân Quang
**Last updated:** 2026-08-07

---

## 1. Purpose

This table is the "single source of truth" for all analysis from Phase 4 onward. Every hypothesis test, bootstrap resampling, segment analysis, and Power BI dashboard reads directly from here — never going back to `dbo.raw_ab_test`.

The row grain is user-level: each unique user occupies exactly 1 row, already deduplicated and with outliers removed per the policy fixed earlier in `preprocessing_checklist.md`.

---

## 2. Column Reference

| # | Column | Type | Nullable | Description | Source | Transformation | Valid values / Range | Example |
|---|---|---|---|---|---|---|---|---|
| 1 | `userid` | `BIGINT` | NO (PK) | The user's unique identifier. Has no business meaning beyond join/identify. | `dbo.raw_ab_test.userid` | Passthrough (after dedup) | Positive integer | `116`, `337`, `377` |
| 2 | `version` | `NVARCHAR(10)` | NO | The A/B group the user is assigned to. `gate_30` = control (gate at level 30), `gate_40` = treatment (gate at level 40). | `dbo.raw_ab_test.version` | Passthrough | `'gate_30'`, `'gate_40'` (CHECK constraint) | `'gate_30'` |
| 3 | `sum_gamerounds` | `INT` | NO | Total number of game rounds the user completed in the first 14 days after install. | `dbo.raw_ab_test.sum_gamerounds` | `MAX()` per userid (POL-1); excluded user = 49854 (POL-3) | 0 ≤ x ≤ ~3,000 (in practice after outlier removal). Max observed: check via VAL-7 | `0`, `38`, `165` |
| 4 | `retention_1` | `BIGINT` | NO | Whether the user returned to the app on day 1 after install. **Caveat:** this metric tracks app opens, not gameplay (see Section 4). | `dbo.raw_ab_test.retention_1` | Passthrough native `BIGINT` (POL-5, no cast to BIT) | `0` = did not return, `1` = returned | `0`, `1` |
| 5 | `retention_7` | `BIGINT` | NO | Whether the user returned to the app on day 7 after install. **Caveat:** same as `retention_1`. | `dbo.raw_ab_test.retention_7` | Passthrough native `BIGINT` (POL-5) | `0`, `1` | `0`, `1` |
| 6 | `log_sum_gamerounds` | `FLOAT` | NO | Natural log transform of `sum_gamerounds`, used for tests assuming near-normality. | Derived | `LOG(1.0 + sum_gamerounds)` (POL-8) | 0 ≤ x ≤ ~8. `LOG(1)=0` when `sum_gamerounds=0`. | `0.0`, `3.66`, `5.11` |
| 7 | `engagement_bucket` | `NVARCHAR(10)` | NO | Engagement grouping by tertile of `sum_gamerounds`. | Derived | `light` if ≤ p33, `medium` if ≤ p67, `heavy` if > p67. Percentiles computed on the whole population after dedup + outlier removal (POL-6, POL-7). | `'light'`, `'medium'`, `'heavy'` (CHECK constraint) | `'light'` |

---

## 3. Constraints & Indexes

| Type | Name | Definition |
|---|---|---|
| Primary Key | `pk_mart_ab_test_base` | `userid` |
| Check | `ck_version` | `version IN ('gate_30', 'gate_40')` |
| Check | `ck_engagement_bucket` | `engagement_bucket IN ('light', 'medium', 'heavy')` |

The table is small (90K rows) → no secondary index needed yet. If Phase 4 runs many queries filtering by `version` or `engagement_bucket`, consider adding a nonclustered index.

---

## 4. Working Assumptions & Caveats

This is what everyone reading/analyzing this table must know:

### 4.1. Retention tracks app opens, not gameplay

The dataset contains **87 users** with `sum_gamerounds = 0` (played no rounds) but `retention_1 = 1` or `retention_7 = 1`. This means the user reopened the app but did not tap play. The working assumption fixed in Phase 2: **the retention metrics track app open sessions, not actual gameplay sessions.**

Impact: when analyzing retention, do not equate it with "player retention" in the gameplay sense. In the final report, distinguish "app retention" vs "gameplay retention".

### 4.2. Outlier removal — only 1 user excluded

The user with `sum_gamerounds = 49,854` (very likely a bot/emulator) was excluded. No other threshold-based filtering was applied — every "smaller" outlier (e.g. users with 2,000-3,000 rounds) was kept as-is.

Impact: the `sum_gamerounds` distribution is still notably right-skewed. Central tendency analysis should prefer median over mean; hypothesis tests for engagement should use Mann-Whitney U or bootstrap instead of a t-test.

### 4.3. No timestamp / session-level data

`sum_gamerounds` is a 14-day total, with no per-day breakdown. It is not possible to compute DAU, MAU, session length, or hourly/daily patterns.

### 4.4. No device / geo / channel segments

The source dataset has no info on device, country, or acquisition channel. Segment analysis can only be done by `engagement_bucket` (derived).

### 4.5. SRM check — chi² = 6.919, p ≈ 0.009 → PASS

The `gate_30 : gate_40` ratio = 49.56% : 50.44%. The chi-square goodness-of-fit test vs H0 = 50/50 passes the α = 0.001 threshold. See `decision_log.md` DEC-01 for the reason behind this strict threshold.

---

## 5. Downstream Usage Guidelines

Recommendations for Phase 4 when querying this table:

- **Retention rate:** `AVG(CAST(retention_1 AS FLOAT))` or `SUM(retention_1) * 1.0 / COUNT(*)` — since `retention_1` is a `BIGINT` 0/1, a direct AVG gives the rate.
- **Median gamerounds:** Use `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sum_gamerounds) OVER (PARTITION BY version)` — remember `SELECT DISTINCT`.
- **Group compare:** Always `GROUP BY version` when comparing the two groups. Don't aggregate the whole table and then conclude about the treatment.
- **Segment analysis:** Crossing `version × engagement_bucket` is the main combo. Remember to check the sample size of each cell before testing — some cells may be too small.
- **Do not add new columns to this table** — if a new derived column is needed, create a view or a new mart, don't modify the source of truth.

---

## 6. Refresh & Rebuild

The table is rebuilt via the script `sql/02_build_mart_ab_test_base.sql`. The script is idempotent (DROP + CREATE + INSERT); re-running it any time yields the same result with the same raw input.

Each rebuild:
1. Writes 1 new record into `cookie_cats.meta_transformation_log`
2. The target row count must = source row count − 1 (due to outlier removal)
3. Run `sql/03_validation_queries.sql` to verify

There is no scheduled refresh — this dataset is static, with no new data coming in.

---

## 7. Change Log

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-08-07 | 1.0 | Initial creation for Phase 3 closure | Xuân Quang |
