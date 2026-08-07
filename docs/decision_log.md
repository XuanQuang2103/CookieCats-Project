# Decision Log

**Project:** Cookie Cats A/B Test Analysis
**Purpose:** Log các quyết định major xuyên project với rationale. Đây là "lịch sử tư duy" — 3 tháng sau đọc lại vẫn hiểu tại sao chọn cách này thay vì cách khác.
**Format:** Architectural Decision Record (ADR) simplified.
**Owner:** Xuân Quang
**Last updated:** 2026-08-07

---

## Cấu trúc mỗi entry

- **Status:** `Accepted` / `Superseded` / `Under review`
- **Date:** ngày ra quyết định
- **Phase:** phase nào quyết định được đưa ra
- **Context:** situation dẫn đến cần quyết định
- **Decision:** chọn cái gì
- **Rationale:** tại sao chọn cái đó
- **Alternatives considered:** đã xem xét gì khác
- **Tradeoffs:** đánh đổi gì để có lợi ích gì
- **Consequences:** hệ quả downstream

---

## DEC-01 — SRM threshold p < 0.001 thay vì 0.05 chuẩn

- **Status:** Accepted
- **Date:** Phase 1 (business understanding), reconfirmed Phase 2
- **Phase:** 2

**Context:**
SRM (Sample Ratio Mismatch) check là gate đầu tiên của A/B test. Ngưỡng α mặc định cho hypothesis testing thường là 0.05. Câu hỏi: nên dùng α nào cho SRM check?

Hai loại error cần cân nhắc:
- **Type I error** (false positive): báo động có SRM trong khi ratio thực ra ổn → false alarm, dừng test oan.
- **Type II error** (false negative): bỏ sót SRM thật (ratio thực sự lệch mà không phát hiện) → toàn bộ analysis downstream invalid. Đây là error đáng sợ nhất về mặt hậu quả.

Lưu ý quan hệ cơ bản: α = P(Type I). Tăng α → dễ reject H0 → Type I tăng nhưng Type II giảm. Nếu chỉ nhìn quan hệ này, muốn giảm Type II (thứ đáng sợ) thì phải **tăng** α, không phải giảm. Đây là điểm counter-intuitive cần giải quyết.

**Decision:**
Sử dụng α = 0.001 (thay vì 0.05) cho SRM chi-square test. Chỉ khi p < 0.001 mới coi là SRM broken.

**Rationale:**
Lý do hạ α (chứ không tăng) nằm ở yếu tố **sample size** mà quan hệ "α vs error" đơn thuần bỏ qua — cụ thể là power của test:

- **Ở n = 90K, power ≈ 100% ngay cả với α = 0.001.** Power (1 − β) phụ thuộc α, effect size, và sample size. Với n rất lớn, test đủ mạnh để detect mọi SRM *meaningful* dù α nhỏ. Nghĩa là hạ α gần như **không làm Type II tăng** cho các SRM đáng lo ngại — sample size lớn đã "gánh" power giùm.
- **Hạ α giải quyết vấn đề thực ở n lớn: Type I / alert fatigue.** Ở n = 90K, chi-square nhạy đến mức deviation trivial (VD 49.7/50.3, không ai quan tâm) cũng ra p < 0.05. Đây là vấn đề statistical significance vs practical significance: ở n lớn mọi thứ đều statistically significant, phải nâng bar để lọc ra cái practically significant. α = 0.001 chỉ báo động khi deviation đủ lớn để nghi structural issue thật.
- **Industry standard:** Microsoft, Booking.com dùng ngưỡng 0.001 hoặc nghiêm hơn cho SRM, chính vì lý do alert fatigue trong high-throughput testing environment (hàng nghìn test/năm).

Tóm gọn: chọn α = 0.001 **không phải** để giảm Type II, mà để giảm Type I — và ta dám làm vậy vì sample size lớn đã giữ Type II thấp giùm rồi.

**Alternatives considered:**
- α = 0.05: ở n = 90K quá nhạy, false positive từ noise trivial liên tục → alert fatigue
- α = 0.01: middle ground nhưng không phổ biến bằng 0.001 trong industry SRM practice
- Tăng α lên >0.05: theo logic "α vs error" thuần túy sẽ giảm Type II, nhưng ở n lớn Type II vốn đã thấp, tăng α chỉ làm Type I tệ hơn → không có lợi

**Tradeoffs:**
- Đánh đổi: về mặt technical, α ↓ → Type II ↑. Nhưng ở n = 90K, mức tăng này negligible cho SRM meaningful (power vẫn ≈100%). Chỉ mất khả năng detect SRM trivial (VD 49.9/50.1) — thứ không impact downstream đáng kể.
- Được: giảm mạnh Type I / false alarm, tránh dừng test oan và escalate không cần thiết.
- **Caveat quan trọng:** rationale này phụ thuộc sample size lớn. Nếu project sau có n nhỏ (VD vài trăm/vài nghìn), power sẽ thấp, lúc đó hạ α = 0.001 khiến Type II tăng đáng kể — nên cân nhắc lại, có thể giữ α cao hơn.

**Consequences:**
- Phase 2 SRM check pass (chi² = 6.902, p = 0.009)
- Phase 3 SRM re-check pass (chi² = 6.919, p ≈ 0.009)
- Phase 4 analysis được tiếp tục hợp lệ

---

## DEC-02 — Keep 87 zero-round-but-retained users

- **Status:** Accepted
- **Date:** Phase 2 (SRM Check, Group 2)
- **Phase:** 2, carried to Phase 3 (POL-2)

**Context:**
Trong dataset có 87 user có `sum_gamerounds = 0` (không chơi vòng nào) nhưng `retention_1 = 1` (29 user còn có `retention_7 = 1`). Hai lựa chọn: (1) coi là data anomaly, exclude; (2) accept là behavior thực và giữ.

**Decision:**
Giữ nguyên 87 user này trong analysis. Document working assumption: **retention metrics track app opens, không phải actual gameplay.**

**Rationale:**
- Đây là behavior explainable: user install → mở app → chưa play → đóng → hôm sau mở lại. App session tồn tại, gameplay session không.
- Loại các user này = throw away 87 data points của behavior thực. Ảnh hưởng đến retention rate estimation.
- Working assumption "retention track app opens" phù hợp với cách nhiều mobile analytics platform (Firebase, Appsflyer) track retention mặc định.

**Alternatives considered:**
- Exclude 87 user: giảm sample size, throw away data không justify được
- Flag riêng: thêm complexity, không lợi ích rõ ràng

**Tradeoffs:**
- Đánh đổi: "retention" trong project này không đồng nghĩa "player retention" theo nghĩa gameplay
- Được: preserve sample size và data integrity

**Consequences:**
- Trong report cuối, phải phân biệt rõ "app retention" vs "gameplay retention"
- Bất kỳ conclusion nào về "player quay lại chơi" phải qualified với caveat này
- Stakeholder deliverables cần có 1 dòng disclaimer về interpretation

---

## DEC-03 — Exclude chỉ 1 outlier user 49,854 rounds

- **Status:** Accepted
- **Date:** Phase 3
- **Phase:** 3 (POL-3, POL-4)

**Context:**
Phase 2 Group 4 (Outlier Analysis) phát hiện 1 user có `sum_gamerounds = 49,854` — cao gấp ~1000 lần median. Trong 14 ngày = 3,561 rounds/ngày = ~148 rounds/giờ liên tục 24/7. Không realistic cho human player.

**Decision:**
Exclude chỉ 1 user duy nhất này. Không apply threshold-based filtering nào khác — mọi user còn lại (kể cả 2,000-3,000 rounds) đều giữ.

**Rationale:**
- Bot/emulator hypothesis strong: 148 rounds/hour continuous không thể là human behavior
- Các outlier "nhỏ hơn" (VD 2,000-3,000 rounds) có thể là legitimate hardcore players — không nên throw away
- Giữ minimum data intervention: mọi filter đều là source of potential bias

**Alternatives considered:**
- **Winsorize ở p99:** đơn giản, standard practice, nhưng throw away signal của legitimate heavy users
- **Dual-track (2 version có/không outlier):** thorough nhất nhưng gấp đôi complexity analysis
- **Không loại gì:** giữ user 49,854, dùng median/non-parametric — nhưng chi² test và mean-based metric sẽ bị distort mạnh

**Tradeoffs:**
- Đánh đổi: 1 record loại có thể tạo bias nhỏ (giảm n gate_30 thêm 1)
- Được: distribution `sum_gamerounds` không còn bị pull bởi outlier extreme; mean/variance metrics reliable hơn

**Consequences:**
- `mart_ab_test_base` có 90,188 rows (raw 90,189 − 1)
- SRM re-check vẫn PASS sau exclude
- Phase 4 vẫn nên ưu tiên non-parametric methods (Mann-Whitney U) cho engagement analysis vì distribution vẫn right-skewed

---

## DEC-04 — Engagement bucket compute trên total population

- **Status:** Accepted
- **Date:** Phase 3
- **Phase:** 3 (POL-6, POL-7)

**Context:**
Cần chia user thành 3 nhóm engagement (light/medium/heavy) theo percentile của `sum_gamerounds`. Hai cách:
- **Cách A:** compute p33/p67 trên toàn population (2 group gộp) → 1 ngưỡng chung
- **Cách B:** compute p33/p67 riêng cho từng group → mỗi group có ngưỡng riêng

**Decision:**
Chọn Cách A — compute percentile trên toàn population sau dedup + outlier removal.

**Rationale:**
- Với A/B test, key question là "gate_30 vs gate_40 khác nhau thế nào". So sánh cần **cùng thước đo** giữa 2 group.
- Cách B tạo "heavy user của gate_30" khác định nghĩa với "heavy user của gate_40" → so sánh cross-group không meaningful.
- Cách A cho phép câu hỏi meaningful: "trong tất cả heavy user, proportion của gate_30 vs gate_40 là bao nhiêu?"

**Alternatives considered:**
- Cách B: hữu ích khi phân tích behavior nội bộ từng group, nhưng không phải use case chính
- Fixed threshold (VD 10, 50, 200 rounds): dễ hiểu nhưng arbitrary, không data-driven

**Tradeoffs:**
- Đánh đổi: nếu 2 group có distribution rất khác nhau, ngưỡng chung có thể mask insight về distribution shift
- Được: comparable buckets, valid cross-group analysis

**Consequences:**
- Bucket distribution có thể lệch nhẹ 33/34/33 do discrete ties tại boundary percentile
- Nếu Phase 4 muốn phân tích thêm góc "heavy user internal to each group", có thể tính bucket riêng như supplementary analysis

---

## DEC-05 — Naming convention: `dbo` cho raw, `cookie_cats` cho analytics

- **Status:** Accepted
- **Date:** Phase 3, Bước 1
- **Phase:** 3

**Context:**
Database `cookie_cats` đã có raw table nằm ở schema `dbo` (`dbo.raw_ab_test`). Cần quyết định layout schema cho các table downstream (mart, meta).

**Decision:**
- Giữ raw table ở `dbo.raw_ab_test`, không di chuyển
- Tạo schema `cookie_cats` trong database `cookie_cats` cho toàn bộ analytics layer
- Prefix: `mart_` cho analysis-ready tables, `meta_` cho audit tables

**Rationale:**
- Ranh giới rõ ràng: `dbo` = external/raw data, `cookie_cats` schema = analysis layer do project team own
- Không cần chạm raw table → giảm risk accidental corruption
- Convention `mart_` / `meta_` prefix inspired bởi dbt và modern data stack practices

**Alternatives considered:**
- Tất cả trong `dbo`: đơn giản hơn nhưng mất ranh giới raw/analytics
- Schema riêng cho `mart` và `meta` (2 schema): overkill cho scope này

**Tradeoffs:**
- Đánh đổi: fully qualified name dài hơn (`cookie_cats.mart_ab_test_base` vs `dbo.mart_ab_test_base`)
- Được: clarity về layer boundary, dễ grant permission theo schema sau này nếu scale

**Consequences:**
- Mọi query downstream (Phase 4, Power BI, notebooks) reference `cookie_cats.mart_ab_test_base`
- Nếu backup, có thể backup riêng schema `cookie_cats` mà không cần raw

---

## DEC-06 — Không cast `retention_1` / `retention_7` sang BIT

- **Status:** Accepted
- **Date:** Phase 3
- **Phase:** 3 (POL-5)

**Context:**
Raw table có `retention_1` và `retention_7` type `BIGINT` với giá trị 0/1. Semantic là biến binary — cast sang `BIT` sẽ đúng semantic hơn và tiết kiệm storage.

**Decision:**
Giữ nguyên native `BIGINT`, không cast sang `BIT`.

**Rationale:**
- Power BI đọc `BIT` như boolean, đôi khi gây rắc rối với DAX aggregation. `BIGINT` đọc trực tiếp là 0/1 và `AVG()` = retention rate dễ dàng.
- pandas đọc `BIGINT` thành `int64` — behavior predictable; `BIT` có thể ra `bool` hoặc `int8` tùy driver, ít consistent.
- Space savings không đáng kể với 90K rows.

**Alternatives considered:**
- Cast sang `BIT`: đúng semantic hơn, nhưng downstream tool compat kém hơn
- Cast sang `TINYINT`: middle ground, nhưng không có lợi ích rõ ràng

**Tradeoffs:**
- Đánh đổi: type không phản ánh chính xác semantic (binary flag stored as BIGINT)
- Được: downstream compatibility với Power BI, pandas, notebooks

**Consequences:**
- Trong `data_dictionary.md`, ghi rõ column là binary flag với domain {0, 1} dù type là `BIGINT`
- Downstream code aggregation: `AVG(CAST(retention_1 AS FLOAT))` để tránh integer division

---

## DEC-07 — Cross-validation giữa SQL và Python cho statistical checks

- **Status:** Accepted (post-incident)
- **Date:** Phase 3 (phát sinh trong quá trình verify VAL-5)
- **Phase:** 3

**Context:**
Trong quá trình chạy VAL-5 (SRM re-check), SQL implementation của công thức chi-square trả về chi² = 13.84 → FAIL, trong khi Phase 2 Python implementation với cùng data cho chi² = 6.902 → PASS. Sau khi debug, phát hiện SQL formula bị bug algebra — thừa hệ số 2.

Root cause: khi derive công thức rút gọn `χ² = k × (n30 - n40)² / n` cho case expected 50/50, tính sai hệ số k. Đúng là k = 1, đã viết thành k = 2.

**Decision:**
Từ giờ, mọi statistical formula viết bằng SQL cho analytical checks phải được cross-validate với reference implementation (scipy/statsmodels) trước khi trust kết quả.

**Rationale:**
- SQL không có unit test framework standard cho statistical formulas
- Công thức "rút gọn" tiết kiệm compute nhưng tăng risk algebra error
- Cost của cross-check thấp (~5 phút), benefit cao (catch bug thầm)

**Alternatives considered:**
- Không cross-check: nhanh hơn nhưng đã chứng minh unsafe
- Dùng luôn scipy trong Python, bỏ SQL statistical checks: mất khả năng data quality gate trong SQL layer

**Tradeoffs:**
- Đánh đổi: thêm 1 bước verify cho mỗi check
- Được: catch được bug tầm này sớm

**Consequences:**
- VAL-5 formula đã fix: `χ² = (n30 - n40)² / n`
- Preventive: các script SQL analytical downstream (Phase 4-6 nếu có) phải có comparison test với Python
- Lesson embedded: user Xuân Quang phát hiện discrepancy nhờ cross-check với Phase 2 output — đây là data science hygiene tốt, giữ tiếp habit này

---

## DEC-08 — Single-layer mart thay vì dual-layer (base + analysis)

- **Status:** Accepted
- **Date:** Phase 3, Bước 1
- **Phase:** 3 (POL-9)

**Context:**
Ban đầu có đề xuất 2-layer: `mart_ab_test_base` (đầy đủ flag, không filter) + `mart_ab_test_analysis` (đã filter theo policy). Cho phép sensitivity analysis "kết quả có đổi không nếu include/exclude outlier?".

**Decision:**
Chốt 1 layer duy nhất: `cookie_cats.mart_ab_test_base` (đã apply toàn bộ policy).

**Rationale:**
- Với scope Cookie Cats (1 outlier duy nhất bị loại), sensitivity analysis không justify overhead 2 layer
- Nếu cần sensitivity, có thể tạm thời rebuild `mart` với policy khác trong Phase 4 rồi rollback
- Đơn giản hơn cho Power BI: 1 source of truth, 1 dataset

**Alternatives considered:**
- 2-layer: robust hơn cho sensitivity analysis, phù hợp scope enterprise
- 0-layer (query raw trực tiếp mỗi lần): không repeatable, không có audit trail

**Tradeoffs:**
- Đánh đổi: mất khả năng nhanh chóng compare "kết quả với vs không outlier"
- Được: simplicity, dễ maintain, downstream clarity

**Consequences:**
- Nếu Phase 4 muốn sensitivity check outlier impact, cần rebuild mart tạm — plan into Phase 4 timeline nếu cần

---

## Ghi chú

- File này sẽ tiếp tục được cập nhật ở Phase 4-7 với các decisions mới (VD threshold cho hypothesis test, choice giữa parametric vs bootstrap, business impact estimation methodology).
- Khi 1 decision bị superseded, giữ nguyên entry cũ và mark `Status: Superseded by DEC-XX`, không delete. Lịch sử tư duy quan trọng bằng conclusion.