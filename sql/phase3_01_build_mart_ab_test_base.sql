--   Step 2: Bước 3 - Build analysis-ready table
--   Purpose: Materialize cookie_cats.mart_ab_test_base with:
--      - Dedup (retain max sum_gamerounds per userid)
--      - Outlier removal (only user with sum_gamerounds = 49854)
--      - Derived columns (log_sum_gamerounds, engagement_bucket)
--   Depends on:  dbo.raw_ab_test, cookie_cats.meta_transformation_log

Use cookie_cats;
Go

-- Step 1: Drop & recreate target table (idempotent rebuild)
-- Rationale: Full rebuild is safe for 90K rows. If we later grow to millions, switch to MERGE pattern.
IF OBJECT_ID('cookie_cats.mart_ab_test_base', 'U') IS NOT NULL
    DROP TABLE cookie_cats.mart_ab_test_base;
GO

CREATE TABLE cookie_cats.mart_ab_test_base (
    userid              BIGINT          NOT NULL,
    version             NVARCHAR(10)    NOT NULL,
    sum_gamerounds      INT             NOT NULL,
    retention_1         BIGINT          NOT NULL,
    retention_7         BIGINT          NOT NULL,
    log_sum_gamerounds  FLOAT           NOT NULL,
    engagement_bucket   NVARCHAR(10)    NOT NULL,
    CONSTRAINT pk_mart_ab_test_base PRIMARY KEY (userid),
    CONSTRAINT ck_version           CHECK (version IN ('gate_30', 'gate_40')),
    CONSTRAINT ck_engagement_bucket CHECK (engagement_bucket IN ('light', 'medium', 'heavy'))
);
GO

DECLARE @src_row_count BIGINT;
DECLARE @tgt_row_count BIGINT;

-- Step 2: Capture source row count BEFORE build
SET @src_row_count = (SELECT COUNT(*) FROM dbo.raw_ab_test);

-- Step 3: Build the mart via CTE pipeline
;WITH dedup AS (
    SELECT 
        userid,
        MAX(version)        AS version,
        MAX(sum_gamerounds) AS sum_gamerounds,
        MAX(retention_1)    AS retention_1,
        MAX(retention_7)    AS retention_7
    FROM dbo.raw_ab_test
    GROUP BY userid
),
filtered AS (
    SELECT *
    FROM dedup
    WHERE sum_gamerounds <> 49854
),
percentiles AS (
    SELECT DISTINCT
        PERCENTILE_CONT(0.33) WITHIN GROUP (ORDER BY sum_gamerounds) OVER() AS p33,
        PERCENTILE_CONT(0.67) WITHIN GROUP (ORDER BY sum_gamerounds) OVER() AS p67
    FROM filtered
),
bucketed AS (
    SELECT
        f.userid,
        f.version,
        f.sum_gamerounds,
        f.retention_1,
        f.retention_7,
        LOG(1.0 + f.sum_gamerounds) AS log_sum_gamerounds,
        CASE
            WHEN f.sum_gamerounds <= p.p33 THEN 'light'
            WHEN f.sum_gamerounds <= p.p67 THEN 'medium'
            ELSE 'heavy'
        END AS engagement_bucket
    FROM filtered f
    CROSS JOIN percentiles p
)
INSERT INTO cookie_cats.mart_ab_test_base (
    userid, version, sum_gamerounds, retention_1, retention_7,
    log_sum_gamerounds, engagement_bucket
)
SELECT
    userid, version, sum_gamerounds, retention_1, retention_7,
    log_sum_gamerounds, engagement_bucket
FROM bucketed;

-- Step 4: Capture target row count AFTER build
SET @tgt_row_count = (SELECT COUNT(*) FROM cookie_cats.mart_ab_test_base);

-- Step 5: Log the transformation
INSERT INTO cookie_cats.meta_transformation_log (
    phase, step_name, source_table, target_table,
    source_row_count, target_row_count, row_delta,
    rule_applied, notes
)
VALUES (
    'Phase 3',
    'Bước 3 - Build mart_ab_test_base',
    'dbo.raw_ab_test',
    'cookie_cats.mart_ab_test_base',
    @src_row_count,
    @tgt_row_count,
    @tgt_row_count - @src_row_count,
    'Dedup: MAX(sum_gamerounds) per userid | '
    + 'Outlier: exclude sum_gamerounds = 49854 | '
    + 'Bucket: light <= p33 < medium <= p67 < heavy (computed on total pop) | '
    + 'Derived: log_sum_gamerounds = LOG(sum_gamerounds + 1)',
    'Full rebuild pattern. Idempotent via DROP+CREATE.'
);
GO       

-- Step 5: Immediate sanity check output
SELECT 'row_count_check' AS check_name,
       (SELECT COUNT(*) FROM dbo.raw_ab_test)                 AS raw_rows,
       (SELECT COUNT(*) FROM cookie_cats.mart_ab_test_base)   AS mart_rows;

SELECT TOP 5 * FROM cookie_cats.mart_ab_test_base ORDER BY userid;

SELECT * FROM cookie_cats.meta_transformation_log
ORDER BY log_id DESC;
GO