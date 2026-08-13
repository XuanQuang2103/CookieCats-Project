"""Load the raw Kaggle CSV into SQL Server table dbo.raw_ab_test.

This automates step 3 of the Reproducibility section (previously a manual
Import Wizard / BULK INSERT step). It is idempotent: re-running with
--truncate rebuilds the table from the file without duplicating rows.

Usage:
    python scripts/load_raw_to_sqlserver.py                  # create + load
    python scripts/load_raw_to_sqlserver.py --truncate       # reload from scratch
    python scripts/load_raw_to_sqlserver.py --csv path/to/cookie_cats.csv

Connection settings come from .env (see README):
    DB_SERVER, DB_NAME, DB_DRIVER, DB_TRUSTED_CONNECTION
    DB_USER, DB_PASSWORD              (only if DB_TRUSTED_CONNECTION=no)

A T-SQL-only alternative is provided in sql/phase3_load_raw_bulk_insert.sql.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "cookie_cats.csv"

# Provenance recorded in sql/phase3_00_create_metadata.sql — the loader refuses
# to load a file whose hash does not match, unless --skip-hash-check is passed.
EXPECTED_MD5 = "99b48ea3d4a552fa6b27aac60a8cfddf"
EXPECTED_ROWS = 90_189
TABLE = "dbo.raw_ab_test"
BATCH_SIZE = 10_000

# retention_1 / retention_7 are stored as BIGINT (binary flag with domain {0,1})
# to stay byte-compatible with the original load — see docs/decision_log.md.
CREATE_TABLE_SQL = """
IF OBJECT_ID('dbo.raw_ab_test', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.raw_ab_test (
        userid          BIGINT        NOT NULL,
        version         NVARCHAR(20)  NOT NULL,
        sum_gamerounds  BIGINT        NOT NULL,
        retention_1     BIGINT        NOT NULL,
        retention_7     BIGINT        NOT NULL
    );
END
"""


def md5_of(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def connect(autocommit: bool = False):
    import pyodbc

    load_dotenv(ROOT / ".env")
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    if not server or not database:
        sys.exit("DB_SERVER / DB_NAME missing — create a .env file (see README).")

    parts = [f"DRIVER={{{driver}}}", f"SERVER={server}", f"DATABASE={database}"]
    if os.getenv("DB_TRUSTED_CONNECTION", "yes").lower() in ("yes", "true", "1"):
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={os.getenv('DB_USER', '')}")
        parts.append(f"PWD={os.getenv('DB_PASSWORD', '')}")
    return pyodbc.connect(";".join(parts) + ";", autocommit=autocommit)


def read_csv(csv_path: Path, skip_hash_check: bool) -> pd.DataFrame:
    if not csv_path.exists():
        sys.exit(
            f"{csv_path} not found. Download the dataset from Kaggle "
            "(yufengsui/mobile-games-ab-testing) and place it in data/."
        )

    actual_md5 = md5_of(csv_path)
    if actual_md5 != EXPECTED_MD5:
        message = (
            f"MD5 mismatch: expected {EXPECTED_MD5}, got {actual_md5}. "
            "The file differs from the one this analysis was built on."
        )
        if not skip_hash_check:
            sys.exit(message + " Pass --skip-hash-check to load anyway.")
        print(f"WARNING: {message}")

    df = pd.read_csv(csv_path)
    expected_cols = ["userid", "version", "sum_gamerounds", "retention_1", "retention_7"]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        sys.exit(f"CSV is missing expected columns: {missing}")

    df = df[expected_cols].copy()
    df["retention_1"] = df["retention_1"].astype(int)
    df["retention_7"] = df["retention_7"].astype(int)
    print(f"CSV read: {len(df):,} rows, md5 = {actual_md5}")
    if len(df) != EXPECTED_ROWS:
        print(f"WARNING: expected {EXPECTED_ROWS:,} raw rows, found {len(df):,}.")
    return df


def load(df: pd.DataFrame, truncate: bool) -> None:
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()

    existing = cursor.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchval()
    if existing and not truncate:
        sys.exit(
            f"{TABLE} already holds {existing:,} rows. "
            "Re-run with --truncate to reload, or drop the table first."
        )
    if truncate and existing:
        cursor.execute(f"TRUNCATE TABLE {TABLE}")
        conn.commit()
        print(f"Truncated {TABLE} ({existing:,} rows removed).")

    cursor.fast_executemany = True
    insert_sql = (
        f"INSERT INTO {TABLE} "
        "(userid, version, sum_gamerounds, retention_1, retention_7) VALUES (?, ?, ?, ?, ?)"
    )
    rows = df.itertuples(index=False, name=None)
    batch: list[tuple] = []
    inserted = 0
    for row in rows:
        batch.append(row)
        if len(batch) == BATCH_SIZE:
            cursor.executemany(insert_sql, batch)
            conn.commit()
            inserted += len(batch)
            print(f"  inserted {inserted:,} / {len(df):,}", end="\r")
            batch = []
    if batch:
        cursor.executemany(insert_sql, batch)
        conn.commit()
        inserted += len(batch)

    final = cursor.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchval()
    print(f"\nLoaded {inserted:,} rows. {TABLE} now holds {final:,} rows.")
    if final != len(df):
        sys.exit("Row count mismatch after load — investigate before running Phase 3 SQL.")

    print("Next: run sql/phase3_00 -> phase3_01 -> phase3_02 to build the mart.")
    cursor.close()
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="path to cookie_cats.csv")
    parser.add_argument("--truncate", action="store_true", help="empty the table before loading")
    parser.add_argument(
        "--skip-hash-check", action="store_true", help="load even if the file MD5 differs"
    )
    args = parser.parse_args()

    df = read_csv(args.csv, args.skip_hash_check)
    load(df, args.truncate)


if __name__ == "__main__":
    main()
