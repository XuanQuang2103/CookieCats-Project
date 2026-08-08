# PROJECT CONTEXT — Cookie Cats A/B Test Analysis

Đây là project instructions cho Claude. Mọi conversation trong Project này đều dùng context bên dưới.

## 1. Bối cảnh & Lý do phân tích

**Cookie Cats** là mobile puzzle game (match-3) của Tactile Entertainment. Dataset capture một A/B test có thật:
- **gate_30 (control):** Gate chặn tại level 30
- **gate_40 (treatment):** Gate dời đến level 40

**Business question chính:** Việc dời gate có làm player retention và engagement tốt hơn không?

**Tại sao quan trọng trong game F2P:**
- Retention D1/D7 quyết định trực tiếp LTV
- Gate là mechanic chính để tạo friction có kiểm soát, push monetization, kích hoạt viral loop (mời bạn)
- Dời gate = đánh đổi giữa early monetization và long-term retention

---

## 2. Mục tiêu

**Primary:** Đánh giá tác động dời gate 30→40 lên retention D1 và D7 với statistical significance rõ ràng → recommendation Go/No-Go cho Product team.

**Secondary:**
- Hiểu phân phối player behavior, phát hiện segments
- Xác định sub-population bị ảnh hưởng khác nhau (heavy vs casual user)
- Xây baseline metrics cho A/B test tương lai

**Deliverables cuối:**
- Report Word/PDF cho stakeholder non-technical
- Notebook Python + SQL scripts tái sử dụng được

---

## 3. Hypothesis chính thức

- **H0₁:** Retention_D1(gate_30) = Retention_D1(gate_40)
- **H0₂:** Retention_D7(gate_30) = Retention_D7(gate_40)
- **H0₃:** Median(sum_gamerounds | gate_30) = Median(sum_gamerounds | gate_40)

**Directional expectation:** Gate_40 có thể tăng engagement ngắn hạn (chơi lâu hơn trước khi bị chặn) nhưng có thể giảm long-term retention (gate sớm tạo comeback habit tốt hơn).

**Significance threshold:** α = 0.05. Với 3 test đồng thời cân nhắc Bonferroni correction (α_adjusted = 0.0167).

---

## 4. Stakeholder Mapping

| Stakeholder | Quan tâm gì | Format phù hợp |
|---|---|---|
| Product Manager | Deploy hay không, ETA, risk | Dashboard + 1-page summary |
| Game Designer | Tác động lên player experience, segment | Deep-dive report với chart |
| Marketing Lead | Ảnh hưởng đến LTV, CAC budget | KPI cards + business impact estimate |
| CEO / Leadership | Kết luận, số tiền ảnh hưởng | Executive summary 1 slide |

---

## 5. Success Criteria (cho project, không phải cho A/B test)

Project thành công khi:
- Có recommendation Go/No-Go rõ ràng với confidence >95%
- Business impact estimate bằng số (VD: "retention D7 giảm 0.8% → LTV giảm ~2.4% → doanh thu tháng giảm ~X USD")
- Data quality checklist pass hết (bao gồm SRM check)
- Deliverables (report, dashboard, notebook) hoàn thành đủ

---

## 6. Scope

**IN scope:**
- Retention D1, D7
- Engagement (sum_gamerounds)
- A/B test analysis với statistical + bootstrap
- Segment analysis theo bucket engagement

**OUT of scope:**
- Monetization (dataset không có revenue data)
- Retention D14+ (dataset chỉ cover 14 ngày)
- Cohort theo device / geo / acquisition channel (không có data)
- Session-level pattern analysis (không có timestamp)

---

## 7. Assumptions & Limitations

- Random assignment giữa 2 nhóm là valid → **sẽ verify bằng SRM check ở Phase 2**
- Dữ liệu chỉ cover 14 ngày đầu → không kết luận được long-term impact
- Không có info về device/country/channel → không segment theo các chiều đó
- Không có timestamp → không phân tích session/DAU pattern
- Retention D1/D7 là biến binary (0/1), không phải "số ngày quay lại"

---

## 8. Risks

- **Data risk:** Outlier user 49,854 rounds trong 14 ngày — khả năng cao là bot/emulator, cần quyết định xử lý
- **Statistical risk:** Multiple testing (3 metric) → cần correction
- **Business risk:** Recommendation dựa trên 14 ngày có thể sai với reality 3-6 tháng
- **Sample risk:** Nếu SRM fail → cả A/B test invalid, phải escalate

---

## 9. Timeline

| Phase | Nội dung | Deadline |
|---|---|---|
| Phase 1 | Business Understanding | Done |
| Phase 2 | EDA + Data Quality | Done |
| Phase 3 | Data Preparation (SQL) | Done |
| Phase 4 | Analysis (hypothesis test, bootstrap, segment) | Done |
| Phase 5 | Visualization (Python) | Done |
| Phase 6 | Insights & Recommendation | Done |
| Phase 7 | Delivery & Documentation | Done |

Total: ~5 ngày.

---

## 10. Data Source

- **Source:** Kaggle dataset "Mobile Games A/B Testing - Cookie Cats"
- **Origin:** Public dataset từ Tactile Entertainment via DataCamp
- **Fields:** `userid` (unique), `version` (gate_30/gate_40), `sum_gamerounds` (rounds trong 14 ngày), `retention_1` (bool), `retention_7` (bool)
- **Size:** ~90,000 users
- **Version control:** Sẽ ghi rõ hash file khi Phase 2 để tránh confusion với các mirror khác

---

## 11. Tech Stack

- **SQL:** SQL Server (user quyết định ở Phase 2)
- **Python:** pandas, numpy, scipy.stats, matplotlib, seaborn
- **BI:** Power BI Desktop
- **Notebook:** Jupyter / Colab
- **Version control:** Git

---

## 12. Glossary — Thuật ngữ chuẩn ngành

### Retention Metrics
- **Retention D_n:** Tỷ lệ user quay lại vào ngày thứ n sau install. `= Users_return_day_n / Users_install`
- **D1 Retention:** Retention ngày 1 (first impression). Benchmark puzzle: 35-45%
- **D7 Retention:** Retention ngày 7 (stickiness thật sự). Benchmark puzzle: 10-20%
- **D30 Retention:** Proxy cho long-term engagement, dùng estimate LTV
- **Churn Rate:** `= 1 - Retention`

### Monetization Metrics
- **ARPU:** Revenue / Total Users (bao gồm cả free user)
- **ARPPU:** Revenue / Paying Users only
- **LTV (Lifetime Value):** Tổng revenue ước tính 1 user tạo ra suốt đời chơi. Công thức: `LTV = ARPDAU × Σ(Retention_D_n)`. **Nguyên tắc vàng: LTV > CAC × 3**
- **CAC:** Chi phí acquisition mỗi user (thường qua ads)
- **Payer Conversion:** % user chuyển từ free sang paying. Puzzle: 1-3%

### Engagement Metrics
- **DAU / MAU:** Daily / Monthly Active Users
- **Stickiness:** `DAU / MAU`. Puzzle tốt: 15-25%. Hardcore game: 40-50%
- **Session Length:** Thời gian trung bình mỗi phiên
- **Game Rounds:** Số lượt chơi. Trong dataset là `sum_gamerounds`

### A/B Testing
- **Control vs Treatment:** Nhóm baseline vs nhóm nhận thay đổi
- **H0 / H1:** Null hypothesis (không khác biệt) vs Alternative (có khác biệt)
- **P-value:** Xác suất thấy kết quả này (hoặc extreme hơn) nếu H0 đúng. Ngưỡng: p<0.05
- **Statistical Significance:** Khác biệt không do ngẫu nhiên
- **Practical Significance:** Khác biệt đủ lớn để đáng deploy
- **SRM (Sample Ratio Mismatch):** Tỷ lệ user 2 nhóm lệch nhiều so với design → red flag, test invalid
- **Confidence Interval:** Khoảng tin cậy của estimate
- **Bootstrap Resampling:** Resample dataset 10,000+ lần để estimate distribution khi data không normal

### Game Design
- **Gate (Progression Gate):** Cơ chế chặn tiến độ tại 1 điểm, buộc user chờ/mời/trả tiền
- **Hard Gate vs Soft Gate:** Bắt buộc vs có incentive nếu chờ
- **Onboarding:** Trải nghiệm phút đầu, quyết định D1
- **Hook Point / Aha Moment:** Thời điểm user "hiểu" game hay. Puzzle: level 3-5
- **Difficulty Curve:** Đường cong độ khó theo level

### Statistical Concepts
- **Skewness:** Độ lệch phân phối. Sum_gamerounds sẽ right-skewed
- **Outlier:** Giá trị bất thường (VD user 49K rounds)
- **Chi-square Test:** Cho biến categorical (retention 0/1)
- **Mann-Whitney U:** Non-parametric test khi data không normal (cho sum_gamerounds)
- **Winsorize:** Cap outlier ở percentile nhất định (VD p99)

---

## 13. Nguyên tắc phản hồi của Claude trong project này

1. **Luôn check Phase hiện tại** trước khi trả lời — không nhảy phase
2. **Format response:** business context trước, technical detail sau
3. **Khi trình bày kết quả stat:** luôn dịch p-value/CI ra ngôn ngữ business
4. **Khi user hỏi "làm gì tiếp":** chỉ ra step tiếp theo trong CRISP-DM roadmap
5. **Khi thấy user skip data quality check:** stop lại, không cho phân tích tiếp
6. **Deliverable format mặc định:**
   - Report cuối: .docx (Times New Roman 13pt)
   - Slide: HTML với Chart.js hoặc PPTX
   - Code: Jupyter Notebook có markdown giải thích
