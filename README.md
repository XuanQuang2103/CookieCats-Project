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

| Phase | Nội dung |
|---|---|
| 1 | Business Understanding |
| 2 | EDA + Data Quality (SRM check, outlier, distribution) |
| 3 | Data Preparation (SQL) |
| 4 | Analysis (hypothesis test, bootstrap, segment) |
| 5 | Visualization (Python + Power BI) |
| 6 | Insights & Recommendation |
| 7 | Delivery & Documentation |

Xem [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) để biết chi tiết scope, assumptions, stakeholder mapping và glossary thuật ngữ chuẩn ngành.
