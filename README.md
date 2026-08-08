# Cookie Cats — Mobile Game A/B Testing Project

Phân tích A/B test cho tựa game puzzle **Cookie Cats** (Tactile Entertainment): đánh giá tác động của việc **dời progression gate từ level 30 sang level 40** lên retention và engagement của người chơi, theo quy trình chuẩn corporate **CRISP-DM**.

## Business Question

> Việc dời gate 30 → 40 có làm **player retention** (D1, D7) và **engagement** tốt hơn không? → Recommendation **Go / No-Go** cho Product team.

## Dataset

- **Nguồn:** Kaggle — *Mobile Games A/B Testing: Cookie Cats* (Tactile Entertainment via DataCamp)
- **Quy mô:** ~90,000 users
- **Fields:**

| Field | Ý nghĩa |
|---|---|
| `userid` | ID duy nhất của người chơi |
| `version` | Nhóm test: `gate_30` (control) / `gate_40` (treatment) |
| `sum_gamerounds` | Số lượt chơi trong 14 ngày đầu |
| `retention_1` | Quay lại sau 1 ngày (bool) |
| `retention_7` | Quay lại sau 7 ngày (bool) |

> ⚠️ File dữ liệu (`data/*.csv`) không được commit lên repo. Tải dataset gốc từ Kaggle và đặt vào `data/`.

## Hypotheses

- **H0₁:** Retention_D1(gate_30) = Retention_D1(gate_40)
- **H0₂:** Retention_D7(gate_30) = Retention_D7(gate_40)
- **H0₃:** Median(sum_gamerounds | gate_30) = Median(sum_gamerounds | gate_40)

Ngưỡng ý nghĩa α = 0.05 (cân nhắc Bonferroni correction α = 0.0167 cho 3 test đồng thời).

## Cấu trúc thư mục

```
.
├── data/            # Dataset (CSV — gitignored)
├── notebooks/       # Jupyter notebooks theo từng phase phân tích
├── reports/         # Chart & báo cáo xuất ra (PNG, ...)
├── sql/             # SQL scripts cho data preparation
├── PROJECT_CONTEXT.md   # Bối cảnh, mục tiêu, scope & glossary chi tiết
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

Cấu hình kết nối database qua file `.env` (xem `.env` mẫu — không commit):

```
DB_SERVER=localhost\SQLEXPRESS
DB_NAME=cookie_cats
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_TRUSTED_CONNECTION=yes
```

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

## Kết luận & Recommendation

> **NO-GO — giữ nguyên gate tại level 30, không triển khai gate 40** (độ tin cậy > 95%).

Ba trụ bằng chứng: (1) retention **D7 giảm 0,82pp (−4,3%)**, có ý nghĩa thống kê vượt cả ngưỡng Bonferroni (p = 0,0016); (2) **engagement bằng nhau** (p = 0,051, bootstrap CI chứa 0) — không có upside để đánh đổi; (3) tác hại tập trung ở nhóm **medium/heavy** (core user), nhóm light gần như không đổi. Tác động kinh doanh proxy (ARPDAU benchmark $0,10): **~818 user D7 mất/tháng trên mỗi 100K installs ≈ $2.454/tháng ≈ $29.448/năm**, tuyến tính theo traffic.

## Deliverables

| Loại | File |
|---|---|
| SQL scripts (idempotent) | `sql/phase3_00_create_metadata.sql`, `sql/phase3_01_build_mart_ab_test_base.sql`, `sql/phase3_02_validation_queries.sql` |
| Notebooks — EDA | `notebooks/phase2_00` → `phase2_04` |
| Notebooks — Analysis | `notebooks/phase4_01_retention` · `phase4_02_Engagement` · `phase4_03_segment` · `phase4_04_business_impact` |
| Report Word — EDA / Data Prep | `reports/CookieCats_Phase2_EDA_Data_Quality_Report.docx`, `reports/CookieCats_Phase3_DataPrepare_Report.docx` |
| Report Word — Analysis | `reports/CookieCats_Phase4_Hypothesis_Testing_Report.docx` |
| Report Word — Insights & Recommendation | `reports/CookieCats_Phase6_Insights_Recommend_Report.docx` |
| Project closeout doc | `reports/CookieCats_Phase7_Closeout-Report.docx` |
| Executive 1-slide (Go/No-Go) | `reports/CookieCats_Executive_Summary.html` |
| Decision log (14 ADR) | `docs/decision_log.md` |
| Data dictionary · Preprocessing checklist | `docs/data_dictionary.md`, `docs/preprocessing_checklist.md` |

## Reproducibility

1. Tạo virtualenv và `pip install -r requirements.txt` (lưu ý: versions dùng `>=`, chưa pin cứng — pin lại nếu cần bản build cố định).
2. Tải `cookie_cats.csv` từ Kaggle, đặt vào `data/` (file bị gitignore, không commit).
3. Load CSV vào SQL Server bảng `dbo.raw_ab_test` (⚠️ hiện chưa có script tự động cho bước load raw này — thực hiện thủ công qua Import Wizard hoặc `BULK INSERT`).
4. Chạy SQL theo thứ tự: `phase3_00` → `phase3_01` → `phase3_02` để dựng `cookie_cats.mart_ab_test_base`.
5. Cấu hình `.env` (xem mẫu bên dưới) rồi chạy notebooks theo thứ tự phase.

> **Ghi chú dọn dẹp:** notebook `phase4_02_Engagement.ipynb` viết hoa chữ E, lệch convention lowercase của các file khác (minor). Bước load raw CSV → `dbo.raw_ab_test` hiện làm thủ công, chưa có script tự động.

Xem [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) để biết chi tiết scope, assumptions, stakeholder mapping và glossary thuật ngữ chuẩn ngành; [`docs/decision_log.md`](docs/decision_log.md) để biết lịch sử các quyết định (14 ADR).
