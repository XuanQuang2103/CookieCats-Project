# Cookie Cats — A/B Testing cho Mobile Game

[English](README.md) · **Tiếng Việt**

Phân tích A/B test cho tựa game puzzle **Cookie Cats** (Tactile Entertainment): việc **dời progression gate từ level 30 sang level 40** có cải thiện retention và engagement của người chơi không? Thực hiện đầy đủ theo quy trình **CRISP-DM**, từ business framing đến recommendation Go/No-Go.

---

## Recommendation: NO-GO — giữ nguyên gate ở level 30

> Không triển khai gate 40. Độ tin cậy > 95%, dựa trên ba trụ bằng chứng độc lập.

| Bằng chứng | Kết quả |
|---|---|
| **Retention D7** | **−0,82pp (−4,3%)**, χ² có hiệu chỉnh Yates, **p = 0,0016** — significant vượt cả ngưỡng Bonferroni α = 0,0167 |
| **Engagement** | **Không khác biệt** — median 17 vs 16 rounds, Mann-Whitney **p = 0,051**, bootstrap 95% CI của median difference chứa 0 → không có upside để đánh đổi phần retention mất đi |
| **Business impact** | **≈ 818 user D7 mất/tháng trên mỗi 100K installs ≈ $2.454/tháng ≈ $29.448/năm** (proxy theo ARPDAU $0,10, tuyến tính theo traffic) |

Tác hại tập trung ở nhóm **medium và heavy** (−0,63pp và −1,27pp trên D7) — chính nhóm tạo ra giá trị — trong khi nhóm light gần như không đổi (+0,11pp). Dời gate ra xa hơn phá vỡ thói quen quay lại của đúng nhóm user đáng giữ nhất.

📄 **Executive summary 1 trang:** [PDF](reports/CookieCats_Executive_Summary_vi.pdf) · [HTML](https://xuanquang2103.github.io/CookieCats-Project/reports/CookieCats_Executive_Summary_vi.html)

---

## Ba biểu đồ mang toàn bộ lập luận

**1. Retention theo nhóm test** — D1 không khác biệt, D7 giảm có ý nghĩa thống kê.

![Retention D1 và D7 theo nhóm, kèm khoảng tin cậy 95%](reports/figures/fig1_retention_by_group.png)

**2. Retention D7 theo engagement segment** — phần mất mát không trải đều mà rơi vào nhóm medium/heavy.

![Retention D7 theo engagement segment](reports/figures/fig2_segment_d7.png)

**3. Phân phối bootstrap của median difference (engagement)** — 95% CI chứa 0, tức không có phần engagement tăng thêm nào để bù cho retention mất đi.

![Phân phối bootstrap của median difference số rounds đã chơi](reports/figures/fig3_bootstrap_median_ci.png)

Cả ba biểu đồ được tạo lại từ dữ liệu gốc bằng `python scripts/export_figures.py`.

---

## Business question

> Việc dời gate 30 → 40 có làm **player retention** (D1, D7) và **engagement** tốt hơn không? → Recommendation **Go / No-Go** cho Product team.

## Dataset

- **Nguồn:** Kaggle — *Mobile Games A/B Testing: Cookie Cats* (Tactile Entertainment via DataCamp)
- **Quy mô:** 90.189 dòng raw → **90.188 user** sau policy dedup và loại outlier
- **Kiểm tra randomisation:** SRM test pass (49,56% / 50,44%, p ≥ 0,001)

| Field | Ý nghĩa |
|---|---|
| `userid` | ID duy nhất của người chơi |
| `version` | Nhóm test: `gate_30` (control) / `gate_40` (treatment) |
| `sum_gamerounds` | Số lượt chơi trong 14 ngày đầu |
| `retention_1` | Quay lại sau 1 ngày (0/1) |
| `retention_7` | Quay lại sau 7 ngày (0/1) |

> ⚠️ File dữ liệu (`data/*.csv`) không được commit lên repo. Tải dataset gốc từ Kaggle và đặt vào `data/`.

## Phương pháp

- **Giả thuyết** — H0₁: retention D1 bằng nhau · H0₂: retention D7 bằng nhau · H0₃: median `sum_gamerounds` bằng nhau
- **Kiểm định** — χ² test of independence có hiệu chỉnh Yates cho hai metric retention; Mann-Whitney U cho engagement (phân phối lệch phải mạnh nên không giả định normality)
- **Multiple testing** — α = 0,05, hiệu chỉnh Bonferroni về α = 0,0167 cho 3 test đồng thời
- **Không chỉ dừng ở p-value** — effect size Cohen's h, 95% CI của hiệu, bootstrap 5.000 lần lặp, và cắt segment theo tertile engagement, để kết luận dựa trên practical significance chứ không chỉ statistical significance

## Cấu trúc thư mục

```
.
├── data/          # Dataset (CSV — gitignored)
├── docs/          # Data dictionary, decision log (14 ADR), checklist, glossary
├── notebooks/     # Jupyter notebooks theo từng phase CRISP-DM
├── reports/       # Report Word, executive summary (HTML + PDF), figures/
├── scripts/       # Script load raw CSV → SQL Server, export biểu đồ
├── sql/           # SQL idempotent cho data preparation
├── PROJECT_CONTEXT.md
├── requirements.txt
└── README.md
```

File có hậu tố `.vi` / `_vi` là bản tiếng Việt của cùng tài liệu đó.

## Tech stack

- **Python** — pandas, numpy, scipy.stats, matplotlib, seaborn
- **SQL** — SQL Server (dựng schema + mart, script idempotent kèm audit trail)
- **Notebook** — Jupyter
- **Tài liệu** — report Word theo từng phase, decision log dạng ADR

## Roadmap (CRISP-DM)

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 1 | Business Understanding | ✅ Done |
| 2 | EDA + Data Quality (SRM check, outlier, distribution) | ✅ Done |
| 3 | Data Preparation (SQL) | ✅ Done |
| 4 | Analysis (hypothesis test, bootstrap, segment) | ✅ Done |
| 5 | Visualization | ⏭️ Bỏ Power BI dashboard (dữ liệu tĩnh — xem DEC-13); report thay thế |
| 6 | Insights & Recommendation | ✅ Done |
| 7 | Delivery & Documentation | ✅ Done |

## Deliverables

| Loại | File |
|---|---|
| Executive 1 trang (Go/No-Go) | [`reports/CookieCats_Executive_Summary_vi.pdf`](reports/CookieCats_Executive_Summary_vi.pdf) |
| Report — Analysis | [`reports/CookieCats_Phase4_Hypothesis_Testing_Report_vi.docx`](reports/CookieCats_Phase4_Hypothesis_Testing_Report_vi.docx) |
| Report — Insights & Recommendation | [`reports/CookieCats_Phase6_Insights_Recommend_Report_vi.docx`](reports/CookieCats_Phase6_Insights_Recommend_Report_vi.docx) |
| Report — EDA / Data Prep | [`reports/CookieCats_Phase2_EDA_Data_Quality_Report_vi.docx`](reports/CookieCats_Phase2_EDA_Data_Quality_Report_vi.docx) · [`reports/CookieCats_Phase3_DataPrepare_Report_vi.docx`](reports/CookieCats_Phase3_DataPrepare_Report_vi.docx) |
| Closeout dự án | [`reports/CookieCats_Phase7_Closeout-Report_vi.docx`](reports/CookieCats_Phase7_Closeout-Report_vi.docx) |
| Notebooks — EDA | `notebooks/phase2_00` → `phase2_04` |
| Notebooks — Analysis | `notebooks/phase4_01_retention_hypothesis_test` · `phase4_02_engagement` · `phase4_03_segment_analysis` · `phase4_04_business_impact` |
| SQL (idempotent) | `sql/phase3_load_raw_bulk_insert.sql` → `phase3_00_create_metadata.sql` → `phase3_01_build_mart_ab_test_base.sql` → `phase3_02_validation_queries.sql` |
| Decision log (14 ADR) | [`docs/decision_log.vi.md`](docs/decision_log.vi.md) |
| Data dictionary · Preprocessing checklist | [`docs/data_dictionary.vi.md`](docs/data_dictionary.vi.md) · [`docs/preprocessing_checklist.vi.md`](docs/preprocessing_checklist.vi.md) |

## Reproducibility

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt   # đã pin version cứng
```

1. Tải `cookie_cats.csv` từ Kaggle, đặt vào `data/` (file bị gitignore).
2. Tạo file `.env` ở thư mục gốc:
   ```
   DB_SERVER=localhost\SQLEXPRESS
   DB_NAME=cookie_cats
   DB_DRIVER=ODBC Driver 17 for SQL Server
   DB_TRUSTED_CONNECTION=yes
   ```
3. Load raw CSV vào `dbo.raw_ab_test` — `python scripts/load_raw_to_sqlserver.py` (script tự đối chiếu MD5 của file với hash provenance đã ghi ở Phase 3; bản thuần T-SQL là `sql/phase3_load_raw_bulk_insert.sql`).
4. Chạy SQL theo thứ tự `phase3_00` → `phase3_01` → `phase3_02` để dựng `cookie_cats.mart_ab_test_base`.
5. Chạy notebooks theo thứ tự phase. Notebook đọc từ SQL Server và tự fallback sang CSV (tái hiện đúng mart policy) nếu chưa cấu hình database — nên phân tích vẫn reproduce được theo cả hai đường.
6. Tạo lại biểu đồ trong README — `python scripts/export_figures.py`.

## Đọc thêm

[`PROJECT_CONTEXT.vi.md`](PROJECT_CONTEXT.vi.md) cho scope, assumptions, stakeholder mapping và glossary thuật ngữ · [`docs/decision_log.vi.md`](docs/decision_log.vi.md) cho 14 quyết định và lý do đằng sau từng quyết định · [`docs/maintenance_notes.md`](docs/maintenance_notes.md) cho phần housekeeping của repo.

## License

[MIT](LICENSE) — phần phân tích và code. Dataset thuộc về tác giả gốc trên Kaggle.
