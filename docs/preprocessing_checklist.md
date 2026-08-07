# Preprocessing Checklist

**Project:** Cookie Cats A/B Test Analysis
**Phase:** 3 — Data Preparation
**Owner:** Xuân Quang
**Status:** Build complete, awaiting sign-off
**Last updated:** 2026-08-07

---

## Mục đích

Tài liệu này gồm 2 phần:

1. **Template** — checklist tái sử dụng được cho bất kỳ project data preparation nào theo CRISP-DM.
2. **Validation Checklist (project-specific)** — checklist cụ thể cho Cookie Cats, list ra từng gate phải pass trước khi sang Phase 4.

---

# PHẦN 1 — TEMPLATE (Reusable)

Dùng làm boilerplate cho mọi project data preparation trong tương lai.

## 1.1. Pre-flight (trước khi động vào data)

- [x] Business context đã được document — có PROJECT_CONTEXT.md hoặc tương đương
- [x] Hypothesis chính thức đã chốt — có H0/H1 rõ ràng, threshold α đã định
- [x] Success criteria đã định nghĩa — biết khi nào project done
- [x] Phase EDA đã completed — có EDA report/findings
- [x] Working assumptions từ EDA đã được carry forward và document
- [x] Decisions về data policy đã chốt bằng văn bản (không giữ trong đầu)

## 1.2. Data Provenance & Version Control

- [x] File source đã có MD5/SHA hash — verify được integrity
- [x] Row count baseline đã ghi lại — so sánh được sau load
- [x] Metadata table đã tạo (`meta_dataset_version` hoặc tương đương)
- [x] 1 record active duy nhất cho version đang dùng
- [ ] Idempotent load — chạy script lại không tạo duplicate metadata

## 1.3. Data Quality Rules (đã chốt trước khi code)

- [x] Deduplication rule — có duplicate không, giữ record nào?
- [x] Missing value policy — drop, impute, hay flag?
- [x] Outlier policy — keep, winsorize, exclude, hay dual-track?
- [x] Anomaly cases — policy là gì?
- [x] Type casting — cast type nào sang type nào? Tại sao?
- [x] Categorical encoding — nếu có, dùng scheme gì?

## 1.4. Feature Engineering (định nghĩa trước khi tạo)

- [x] Danh sách derived columns đã chốt
- [x] Bucketing/binning cutoff đã định — dùng percentile nào, tính trên population nào?
- [x] Transformation formula đã document (log, sqrt, standardize, ...)
- [x] Cross-group vs within-group logic đã cân nhắc — quan trọng với A/B test

## 1.5. Build & Materialize

- [x] Table target có primary key — đảm bảo unique
- [x] Table có CHECK constraint cho categorical column
- [x] Script idempotent — chạy lại không hỏng data
- [x] Full rebuild vs incremental — chọn strategy phù hợp scale
- [x] Transformation log đã insert — audit trail đầy đủ

## 1.6. Documentation

- [x] Data dictionary cho target table
- [x] Transformation notes — từng bước làm gì, tại sao
- [x] Decision log — mỗi quyết định policy có rationale
- [x] SQL scripts có comment

## 1.7. Validation (Gate cuối)

- [x] Row count reconciliation
- [x] No unexpected duplicates
- [x] No unexpected NULLs
- [x] Distribution sanity check
- [x] Randomization re-check (SRM)
- [x] Categorical bucket distribution hợp lý
- [x] Business metrics preview

**Rule cứng: nếu bất kỳ gate nào FAIL → không được sang phase tiếp theo.**

---

# PHẦN 2 — VALIDATION CHECKLIST (Cookie Cats A/B Test)

## 2.1. Pre-flight

| # | Check | Expected | Actual | Status |
|---|---|---|---|---|
| P1 | PROJECT_CONTEXT.md tồn tại | Root project | ✅ Present | ✅ |
| P2 | Phase 2 EDA hoàn thành | 4 groups + report | ✅ Done | ✅ |
| P3 | Working assumptions đã ghi | 87 zero-round users | ✅ Documented | ✅ |
| P4 | Hypothesis formal | H0₁, H0₂, H0₃ với α=0.05 | ✅ | ✅ |
| P5 | SRM threshold agreed | p < 0.001 | ✅ | ✅ |

## 2.2. Data Provenance

| # | Check | Expected | Actual | Status |
|---|---|---|---|---|
| D1 | MD5 hash raw file | `99b48ea3d4a552fa6b27aac60a8cfddf` | Confirmed via metadata | ✅ |
| D2 | Raw row count | 90,189 | 90,189 | ✅ |
| D3 | Raw column count | 5 | 5 | ✅ |
| D4 | 1 active metadata record | 1 row is_active=1 | 1 row | ✅ |
| D5 | target_table field | `dbo.raw_ab_test` | `dbo.raw_ab_test` | ✅ |

## 2.3. Data Policy Decisions (reference chính thức)

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

Thực hiện qua `sql/03_validation_queries.sql`.

| # | Check | Expected | Actual | Status |
|---|---|---|---|---|
| VAL-1 | Row count reconciliation | mart_rows = 90,188 | 90,188 | ✅ |
| VAL-2 | Duplicate userids | 0 | 0 | ✅ |
| VAL-3 | User 49854 rounds present | 0 | 0 | ✅ |
| VAL-4 | NULLs in mart | 0 | 0 | ✅ |
| VAL-5 | SRM re-check | chi² < 10.828 (p ≥ 0.001) | ~6.92 | ✅ |
| VAL-6 | Bucket distribution | ~33/34/33 | ~33/34/33 | ✅ |
| VAL-7 | sum_gamerounds stats vs Phase 2 | khớp EDA (minus outlier) | Khớp | ✅ |s
| VAL-8 | Retention baseline | D1 ~44%, D7 ~18% |D1 ~44%, D7 ~18%| ✅ |

## 2.5. Documentation Artifacts

| # | Artifact | Location | Status |
|---|---|---|---|
| DOC-1 | `preprocessing_checklist.md` | `docs/` | ✅ (this file) |
| DOC-2 | `data_dictionary.md` cho `mart_ab_test_base` | `docs/` | ⏳ Pending |
| DOC-3 | `decision_log.md` — log các quyết định policy xuyên project | `docs/` | ⏳ Pending |
| DOC-4 | `01_metadata_setup.sql` (Bước 2) | `sql/` | ✅ Executed |
| DOC-5 | `02_build_mart_ab_test_base.sql` (Bước 3) | `sql/` | ✅ Executed |
| DOC-6 | `03_validation_queries.sql` | `sql/` | ✅ Executed |
| DOC-7 | Transformation log populated | `cookie_cats.meta_transformation_log` | ✅ |

## 2.6. Sign-off

Không sang Phase 4 cho đến khi:

- [x] Tất cả VAL-1 → VAL-8 status = ✅ PASS
- [ ] Data dictionary (DOC-2) hoàn thành
- [ ] Decision log (DOC-3) hoàn thành
- [ ] Section 2.4 (Actual) đã fill số cụ thể (tùy chọn nhưng khuyến nghị)
- [ ] Bản checklist này commit vào repo

**Approver:** Xuân Quang
**Sign-off date:** 2026-08-07


