# Preprocessing Checklist

**Project:** Cookie Cats A/B Test Analysis
**Phase:** 3 — Data Preparation
**Owner:** Xuân Quang
**Status:** Build complete, awaiting sign-off
**Last updated:** 2026-08-07

---

## Purpose

This document has 2 parts:

1. **Template** — a reusable checklist for any data preparation project following CRISP-DM.
2. **Validation Checklist (project-specific)** — the specific checklist for Cookie Cats, listing each gate that must pass before moving to Phase 4.

---

# PART 1 — TEMPLATE (Reusable)

Use as boilerplate for every future data preparation project.

## 1.1. Pre-flight (before touching the data)

- [x] Business context is documented — has PROJECT_CONTEXT.md or equivalent
- [x] Formal hypotheses are fixed — has clear H0/H1, threshold α defined
- [x] Success criteria are defined — you know when the project is done
- [x] EDA phase is completed — has an EDA report/findings
- [x] Working assumptions from EDA are carried forward and documented
- [x] Data policy decisions are fixed in writing (not kept in your head)

## 1.2. Data Provenance & Version Control

- [x] Source file has an MD5/SHA hash — integrity is verifiable
- [x] Baseline row count is recorded — comparable after load
- [x] Metadata table created (`meta_dataset_version` or equivalent)
- [x] Exactly 1 active record for the version in use
- [ ] Idempotent load — re-running the script does not create duplicate metadata

## 1.3. Data Quality Rules (fixed before coding)

- [x] Deduplication rule — are there duplicates, which record to keep?
- [x] Missing value policy — drop, impute, or flag?
- [x] Outlier policy — keep, winsorize, exclude, or dual-track?
- [x] Anomaly cases — what is the policy?
- [x] Type casting — cast which type to which type? Why?
- [x] Categorical encoding — if any, which scheme?

## 1.4. Feature Engineering (defined before creation)

- [x] The list of derived columns is fixed
- [x] Bucketing/binning cutoffs are defined — which percentile, computed on which population?
- [x] Transformation formulas are documented (log, sqrt, standardize, ...)
- [x] Cross-group vs within-group logic is considered — important for A/B tests

## 1.5. Build & Materialize

- [x] The target table has a primary key — ensures uniqueness
- [x] The table has a CHECK constraint for categorical columns
- [x] The script is idempotent — re-running does not corrupt the data
- [x] Full rebuild vs incremental — choose the strategy suited to scale
- [x] Transformation log is inserted — a complete audit trail

## 1.6. Documentation

- [x] Data dictionary for the target table
- [x] Transformation notes — what each step does, why
- [x] Decision log — each policy decision has a rationale
- [x] SQL scripts are commented

## 1.7. Validation (Final Gate)

- [x] Row count reconciliation
- [x] No unexpected duplicates
- [x] No unexpected NULLs
- [x] Distribution sanity check
- [x] Randomization re-check (SRM)
- [x] Categorical bucket distribution is reasonable
- [x] Business metrics preview

**Hard rule: if any gate FAILS → you may not move to the next phase.**

---

# PART 2 — VALIDATION CHECKLIST (Cookie Cats A/B Test)

## 2.1. Pre-flight

| # | Check | Expected | Actual | Status |
|---|---|---|---|---|
| P1 | PROJECT_CONTEXT.md exists | Project root | ✅ Present | ✅ |
| P2 | Phase 2 EDA completed | 4 groups + report | ✅ Done | ✅ |
| P3 | Working assumptions recorded | 87 zero-round users | ✅ Documented | ✅ |
| P4 | Formal hypotheses | H0₁, H0₂, H0₃ with α=0.05 | ✅ | ✅ |
| P5 | SRM threshold agreed | p < 0.001 | ✅ | ✅ |

## 2.2. Data Provenance

| # | Check | Expected | Actual | Status |
|---|---|---|---|---|
| D1 | MD5 hash of raw file | `99b48ea3d4a552fa6b27aac60a8cfddf` | Confirmed via metadata | ✅ |
| D2 | Raw row count | 90,189 | 90,189 | ✅ |
| D3 | Raw column count | 5 | 5 | ✅ |
| D4 | 1 active metadata record | 1 row is_active=1 | 1 row | ✅ |
| D5 | target_table field | `dbo.raw_ab_test` | `dbo.raw_ab_test` | ✅ |

## 2.3. Data Policy Decisions (official reference)

| # | Decision | Chosen policy |
|---|---|---|
| POL-1 | Deduplication | `MAX(sum_gamerounds)` per `userid` |
| POL-2 | 87 zero-round-but-retained users | Keep as-is (working assumption: retention tracks app opens) |
| POL-3 | Outlier `sum_gamerounds = 49854` | Exclude (single confirmed bot/emulator suspicion) |
| POL-4 | Other outliers | Keep (no threshold-based filtering) |
| POL-5 | `retention_1` / `retention_7` type | Keep native `BIGINT` (no cast) |
| POL-6 | `engagement_bucket` cutoff | `light ≤ p33 < medium ≤ p67 < heavy` |
| POL-7 | Percentile computed on | Total population (both gates combined) |
| POL-8 | `log_sum_gamerounds` formula | `LOG(1.0 + sum_gamerounds)` (natural log) |
| POL-9 | Table layer | Single: `cookie_cats.mart_ab_test_base` |

## 2.4. Build Validation

Performed via `sql/03_validation_queries.sql`.

| # | Check | Expected | Actual | Status |
|---|---|---|---|---|
| VAL-1 | Row count reconciliation | mart_rows = 90,188 | 90,188 | ✅ |
| VAL-2 | Duplicate userids | 0 | 0 | ✅ |
| VAL-3 | User 49854 rounds present | 0 | 0 | ✅ |
| VAL-4 | NULLs in mart | 0 | 0 | ✅ |
| VAL-5 | SRM re-check | chi² < 10.828 (p ≥ 0.001) | ~6.92 | ✅ |
| VAL-6 | Bucket distribution | ~33/34/33 | ~33/34/33 | ✅ |
| VAL-7 | sum_gamerounds stats vs Phase 2 | matches EDA (minus outlier) | Matches | ✅ |s
| VAL-8 | Retention baseline | D1 ~44%, D7 ~18% |D1 ~44%, D7 ~18%| ✅ |

## 2.5. Documentation Artifacts

| # | Artifact | Location | Status |
|---|---|---|---|
| DOC-1 | `preprocessing_checklist.md` | `docs/` | ✅ (this file) |
| DOC-2 | `data_dictionary.md` for `mart_ab_test_base` | `docs/` | ✅ Executed |
| DOC-3 | `decision_log.md` — log of policy decisions across the project | `docs/` | ✅ Executed |
| DOC-4 | `01_metadata_setup.sql` (Step 2) | `sql/` | ✅ Executed |
| DOC-5 | `02_build_mart_ab_test_base.sql` (Step 3) | `sql/` | ✅ Executed |
| DOC-6 | `03_validation_queries.sql` | `sql/` | ✅ Executed |
| DOC-7 | Transformation log populated | `cookie_cats.meta_transformation_log` | ✅ |

## 2.6. Sign-off

Do not move to Phase 4 until:

- [x] All VAL-1 → VAL-8 status = ✅ PASS
- [x] Data dictionary (DOC-2) completed
- [x] Decision log (DOC-3) completed
- [x] Section 2.4 (Actual) filled with concrete numbers (optional but recommended)
- [x] This checklist is committed to the repo

**Approver:** Xuân Quang
**Sign-off date:** 2026-08-07
