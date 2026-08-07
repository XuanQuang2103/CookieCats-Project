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

Table này là "single source of truth" cho toàn bộ analysis từ Phase 4 trở đi. Tất cả hypothesis test, bootstrap resampling, segment analysis, và Power BI dashboard đều đọc trực tiếp từ đây — không quay lại `dbo.raw_ab_test`.

Row grain là user-level: mỗi user duy nhất chiếm đúng 1 row, đã được dedup và loại outlier theo policy chốt trước ở `preprocessing_checklist.md`.

---

## 2. Column Reference

| # | Column | Type | Nullable | Description | Source | Transformation | Valid values / Range | Example |
|---|---|---|---|---|---|---|---|---|
| 1 | `userid` | `BIGINT` | NO (PK) | Định danh duy nhất của user. Không có ý nghĩa business ngoài việc join/identify. | `dbo.raw_ab_test.userid` | Passthrough (sau dedup) | Positive integer | `116`, `337`, `377` |
| 2 | `version` | `NVARCHAR(10)` | NO | Nhóm A/B mà user được assign. `gate_30` = control (gate tại level 30), `gate_40` = treatment (gate tại level 40). | `dbo.raw_ab_test.version` | Passthrough | `'gate_30'`, `'gate_40'` (CHECK constraint) | `'gate_30'` |
| 3 | `sum_gamerounds` | `INT` | NO | Tổng số vòng chơi (game rounds) mà user hoàn thành trong 14 ngày đầu sau install. | `dbo.raw_ab_test.sum_gamerounds` | `MAX()` per userid (POL-1); loại user = 49854 (POL-3) | 0 ≤ x ≤ ~3,000 (thực tế sau outlier removal). Max quan sát: kiểm tra qua VAL-7 | `0`, `38`, `165` |
| 4 | `retention_1` | `BIGINT` | NO | User có quay lại app vào ngày 1 sau install không. **Caveat:** metric này track app open, không phải gameplay (xem Section 4). | `dbo.raw_ab_test.retention_1` | Passthrough native `BIGINT` (POL-5, không cast BIT) | `0` = không quay lại, `1` = quay lại | `0`, `1` |
| 5 | `retention_7` | `BIGINT` | NO | User có quay lại app vào ngày 7 sau install không. **Caveat:** như `retention_1`. | `dbo.raw_ab_test.retention_7` | Passthrough native `BIGINT` (POL-5) | `0`, `1` | `0`, `1` |
| 6 | `log_sum_gamerounds` | `FLOAT` | NO | Natural log transform của `sum_gamerounds`, dùng cho các test giả định gần-normal. | Derived | `LOG(1.0 + sum_gamerounds)` (POL-8) | 0 ≤ x ≤ ~8. `LOG(1)=0` khi `sum_gamerounds=0`. | `0.0`, `3.66`, `5.11` |
| 7 | `engagement_bucket` | `NVARCHAR(10)` | NO | Phân nhóm engagement theo tertile của `sum_gamerounds`. | Derived | `light` nếu ≤ p33, `medium` nếu ≤ p67, `heavy` nếu > p67. Percentile compute trên toàn population sau dedup + outlier removal (POL-6, POL-7). | `'light'`, `'medium'`, `'heavy'` (CHECK constraint) | `'light'` |

---

## 3. Constraints & Indexes

| Type | Name | Definition |
|---|---|---|
| Primary Key | `pk_mart_ab_test_base` | `userid` |
| Check | `ck_version` | `version IN ('gate_30', 'gate_40')` |
| Check | `ck_engagement_bucket` | `engagement_bucket IN ('light', 'medium', 'heavy')` |

Table nhỏ (90K rows) → chưa cần thêm secondary index. Nếu Phase 4 chạy nhiều query filter theo `version` hoặc `engagement_bucket`, cân nhắc add nonclustered index.

---

## 4. Working Assumptions & Caveats

Đây là điều mọi người đọc/phân tích bảng này phải biết:

### 4.1. Retention tracks app opens, không phải gameplay

Trong dataset có **87 user** với `sum_gamerounds = 0` (không chơi vòng nào) nhưng `retention_1 = 1` hoặc `retention_7 = 1`. Nghĩa là user mở app quay lại nhưng không bấm play. Working assumption chốt ở Phase 2: **các metric retention track app open sessions, không phải actual gameplay sessions.**

Impact: khi phân tích retention, không được equate với "player retention" theo nghĩa gameplay. Trong report cuối, phải phân biệt "app retention" vs "gameplay retention".

### 4.2. Outlier removal — chỉ 1 user bị loại

User có `sum_gamerounds = 49,854` (khả năng cao là bot/emulator) đã bị exclude. Không apply threshold-based filtering nào khác — mọi outlier "nhỏ hơn" (VD user 2,000-3,000 rounds) đều giữ nguyên.

Impact: distribution `sum_gamerounds` vẫn right-skewed đáng kể. Phân tích central tendency nên ưu tiên median hơn mean; hypothesis test cho engagement nên dùng Mann-Whitney U hoặc bootstrap thay vì t-test.

### 4.3. Không có timestamp / session-level data

`sum_gamerounds` là total 14 ngày, không có breakdown theo ngày. Không thể tính DAU, MAU, session length, hoặc pattern theo giờ/ngày.

### 4.4. Không có segment device / geo / channel

Dataset gốc không có info về device, country, hoặc acquisition channel. Segment analysis chỉ có thể theo `engagement_bucket` (derived).

### 4.5. SRM check — chi² = 6.919, p ≈ 0.009 → PASS

Ratio `gate_30 : gate_40` = 49.56% : 50.44%. Chi-square goodness-of-fit test vs H0 = 50/50 pass ngưỡng α = 0.001. Xem `decision_log.md` DEC-01 để biết lý do dùng ngưỡng nghiêm ngặt này.

---

## 5. Downstream Usage Guidelines

Recommendation cho Phase 4 khi query table này:

- **Retention rate:** `AVG(CAST(retention_1 AS FLOAT))` hoặc `SUM(retention_1) * 1.0 / COUNT(*)` — vì `retention_1` là `BIGINT` 0/1 nên AVG trực tiếp cho tỷ lệ.
- **Median gamerounds:** Dùng `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sum_gamerounds) OVER (PARTITION BY version)` — nhớ `SELECT DISTINCT`.
- **Group compare:** Luôn `GROUP BY version` khi so sánh 2 group. Đừng aggregate toàn table rồi kết luận về treatment.
- **Segment analysis:** Cross `version × engagement_bucket` là combo chính. Nhớ check sample size mỗi cell trước khi test — vài cell có thể quá nhỏ.
- **Không thêm column mới vào table này** — nếu cần derived column mới, tạo view hoặc mart mới, đừng modify source of truth.

---

## 6. Refresh & Rebuild

Table được rebuild bằng script `sql/02_build_mart_ab_test_base.sql`. Script idempotent (DROP + CREATE + INSERT), chạy lại bất cứ lúc nào cũng ra cùng kết quả với cùng raw input.

Mỗi lần rebuild:
1. Ghi 1 record mới vào `cookie_cats.meta_transformation_log`
2. Row count target phải = row count source − 1 (do loại outlier)
3. Chạy `sql/03_validation_queries.sql` để verify

Không có scheduled refresh — dataset này static, không có new data coming in.

---

## 7. Change Log

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-08-07 | 1.0 | Initial creation cho Phase 3 closure | Xuân Quang |
