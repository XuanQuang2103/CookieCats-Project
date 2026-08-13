-- Phase 3 - Step 0: Load the raw Kaggle CSV into dbo.raw_ab_test
-- Purpose: T-SQL alternative to scripts/load_raw_to_sqlserver.py (no Python needed).
-- Run this BEFORE phase3_00_create_metadata.sql.
--
-- Prerequisites:
--   1. Database [cookie_cats] exists.
--   2. cookie_cats.csv is readable BY THE SQL SERVER SERVICE ACCOUNT
--      (a local path on the server machine, not a client-side path).
--      Adjust @csv_path below.
--   3. The SQL Server service account has ADMINISTER BULK OPERATIONS
--      (or you are a member of bulkadmin).
--
-- Idempotent: the table is created only if missing and truncated before load,
-- so re-running always yields exactly the file's row count.

USE cookie_cats;
GO

-- Step 1: Create the raw landing table if it does not exist.
-- retention_1 / retention_7 are BIGINT binary flags with domain {0, 1}
-- (kept as loaded from source — see docs/decision_log.md).
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
GO

-- Step 2: Empty the table so the load is repeatable.
TRUNCATE TABLE dbo.raw_ab_test;
GO

-- Step 3: Bulk load. Edit the path to match your machine.
BULK INSERT dbo.raw_ab_test
FROM 'C:\path\to\repo\data\cookie_cats.csv'
WITH (
    FIRSTROW        = 2,            -- skip the header row
    FIELDTERMINATOR = ',',
    ROWTERMINATOR   = '0x0a',       -- LF; use '\n' if the file has CRLF endings
    CODEPAGE        = '65001',      -- UTF-8
    TABLOCK,
    MAXERRORS       = 0
);
GO

-- Step 4: Sanity check — the source file has 90,189 raw rows
--         (90,188 users remain in the mart after the outlier policy).
SELECT 'raw_load_check'                     AS check_name,
       COUNT(*)                             AS raw_rows,
       COUNT(DISTINCT userid)               AS distinct_users,
       SUM(CASE WHEN version NOT IN ('gate_30', 'gate_40') THEN 1 ELSE 0 END) AS bad_version_rows,
       SUM(CASE WHEN retention_1 NOT IN (0, 1)
                  OR retention_7 NOT IN (0, 1) THEN 1 ELSE 0 END)             AS bad_flag_rows
FROM dbo.raw_ab_test;
GO
