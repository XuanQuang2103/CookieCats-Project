-- Phase 3 - Step 1: Metadata setup
-- Purpose: Establish data provenance & audit trail

USE cookie_cats;   
GO

-- Bước 1: Tạo schema 
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'cookie_cats')
    EXEC('CREATE SCHEMA cookie_cats');
GO

-- Bước 2: Tạo meta_dataset_version 
IF OBJECT_ID('cookie_cats.meta_dataset_version', 'U') IS NULL
BEGIN
    EXEC('
        CREATE TABLE cookie_cats.meta_dataset_version (
            version_id         INT IDENTITY(1,1) PRIMARY KEY,
            dataset_name       NVARCHAR(100)  NOT NULL,
            source_type        NVARCHAR(50)   NOT NULL,
            source_reference   NVARCHAR(500)  NOT NULL,
            source_file_name   NVARCHAR(255)  NOT NULL,
            md5_hash           CHAR(32)       NOT NULL,
            row_count          BIGINT         NOT NULL,
            column_count       INT            NOT NULL,
            target_table       NVARCHAR(200)  NOT NULL,
            loaded_at_utc      DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),
            loaded_by          NVARCHAR(100)  NOT NULL DEFAULT SUSER_SNAME(),
            is_active          BIT            NOT NULL DEFAULT 1,
            notes              NVARCHAR(1000) NULL
        );
    ');
END
GO

-- Bước 3: Tạo meta_transformation_log
IF OBJECT_ID('cookie_cats.meta_transformation_log', 'U') IS NULL
BEGIN
    EXEC('
        CREATE TABLE cookie_cats.meta_transformation_log (
            log_id             INT IDENTITY(1,1) PRIMARY KEY,
            phase              NVARCHAR(20)   NOT NULL,
            step_name          NVARCHAR(200)  NOT NULL,
            source_table       NVARCHAR(200)  NOT NULL,
            target_table       NVARCHAR(200)  NOT NULL,
            source_row_count   BIGINT         NOT NULL,
            target_row_count   BIGINT         NOT NULL,
            row_delta          BIGINT         NOT NULL,
            rule_applied       NVARCHAR(1000) NOT NULL,
            executed_at_utc    DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),
            executed_by        NVARCHAR(100)  NOT NULL DEFAULT SUSER_SNAME(),
            notes              NVARCHAR(1000) NULL
        );
    ');
END
GO

-- Bước 4: Verify 2 table đã tạo
SELECT
    s.name AS schema_name,
    t.name AS table_name,
    t.create_date
FROM sys.tables t
JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE s.name = 'cookie_cats'
ORDER BY t.name;
GO


-- Ghi metadata cho raw dataset
INSERT INTO cookie_cats.meta_dataset_version (
    dataset_name, source_type, source_reference, source_file_name,
    md5_hash, row_count, column_count, target_table, notes
)
SELECT
    'Cookie Cats A/B Test',
    'kaggle',
    'https://www.kaggle.com/datasets/yufengsui/mobile-games-ab-testing',
    'cookie_cats.csv',
    '99b48ea3d4a552fa6b27aac60a8cfddf',
    (SELECT COUNT(*) FROM dbo.raw_ab_test),
    5,
    'dbo.raw_ab_test',
    'Raw load for Phase 3. Verified against Phase 2 EDA. '
    + 'Dedup policy: retain max sum_gamerounds per user. '
    + '87 zero-round-but-retained users: keep as-is (working assumption: retention tracks app open). '
    + 'Outlier policy: exclude only user with sum_gamerounds = 49854; keep all others.'
WHERE NOT EXISTS (
    SELECT 1 FROM cookie_cats.meta_dataset_version
    WHERE md5_hash = '99b48ea3d4a552fa6b27aac60a8cfddf' AND is_active = 1
);
GO

-- Verify
SELECT
    version_id,
    dataset_name,
    md5_hash,
    row_count,
    column_count,
    target_table,
    is_active,
    loaded_at_utc,
    loaded_by
FROM cookie_cats.meta_dataset_version
ORDER BY version_id DESC;
GO

