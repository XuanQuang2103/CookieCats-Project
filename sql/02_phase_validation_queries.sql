--   Purpose:     Verify mart_ab_test_base is analysis-ready
--                Run AFTER 02_build_mart_ab_test_base.sql
--   Rule:        If ANY check fails, DO NOT proceed to Phase 4

USE cookie_cats;
GO

-- VAL-1: Row count reconciliation
-- Expected: raw_rows = 90189
--             mart_rows = 90188  (raw - 1 outlier user, no duplicates in this dataset)
--             row_delta = -1
PRINT '--- VAL-1: Row count reconciliation ---';
SELECT
    (SELECT COUNT(*) FROM dbo.raw_ab_test)                AS raw_rows,
    (SELECT COUNT(*) FROM cookie_cats.mart_ab_test_base)  AS mart_rows,
    (SELECT COUNT(*) FROM cookie_cats.mart_ab_test_base)
        - (SELECT COUNT(*) FROM dbo.raw_ab_test)          AS row_delta,
    CASE
        WHEN (SELECT COUNT(*) FROM cookie_cats.mart_ab_test_base)
             = (SELECT COUNT(*) FROM dbo.raw_ab_test) - 1
        THEN 'PASS'
        ELSE 'FAIL - investigate'
    END AS verdict;
GO

-- VAL-2: No duplicate userids in mart
--   Expected: 0 duplicates
 
PRINT '--- VAL-2: Duplicate userid check ---';
SELECT
    COUNT(*) AS duplicate_userids,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS verdict
FROM (
    SELECT userid
    FROM cookie_cats.mart_ab_test_base
    GROUP BY userid
    HAVING COUNT(*) > 1
) as duplicates;
GO


--   VAL-3: Outlier user (49,854 rounds) removed
--   Expected: 0 rows with sum_gamerounds = 49854

PRINT '--- VAL-3: Outlier removal check ---';
SELECT
    COUNT(*) AS extreme_outlier_rows,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS verdict
FROM cookie_cats.mart_ab_test_base
WHERE sum_gamerounds = 49854;
GO


--   VAL-4: No NULLs in any column
--   Expected: 0 NULLs across all columns

PRINT '--- VAL-4: NULL check ---';
SELECT
    SUM(CASE WHEN userid             IS NULL THEN 1 ELSE 0 END) AS null_userid,
    SUM(CASE WHEN version            IS NULL THEN 1 ELSE 0 END) AS null_version,
    SUM(CASE WHEN sum_gamerounds     IS NULL THEN 1 ELSE 0 END) AS null_sum_gamerounds,
    SUM(CASE WHEN retention_1        IS NULL THEN 1 ELSE 0 END) AS null_retention_1,
    SUM(CASE WHEN retention_7        IS NULL THEN 1 ELSE 0 END) AS null_retention_7,
    SUM(CASE WHEN log_sum_gamerounds IS NULL THEN 1 ELSE 0 END) AS null_log_sum,
    SUM(CASE WHEN engagement_bucket  IS NULL THEN 1 ELSE 0 END) AS null_bucket
FROM cookie_cats.mart_ab_test_base;
GO


--   VAL-5: Version distribution (SRM re-check)
--   Expected: chi-square p-value >= 0.001 (threshold from Phase 2)
--   Chi-square manual approximation on 50/50 expected split:
--     Under H0 (50/50), expected count per group = n/2
--     Chi² = 2 * (count_30 - count_40)^2 / n     (algebraic simplification)

PRINT '--- VAL-5: SRM re-check (chi-square approx) ---';
;WITH counts AS (
    SELECT
        SUM(CASE WHEN version = 'gate_30' THEN 1 ELSE 0 END) AS n30,
        SUM(CASE WHEN version = 'gate_40' THEN 1 ELSE 0 END) AS n40,
        COUNT(*) AS n_total
    FROM cookie_cats.mart_ab_test_base
)
SELECT
    n30,
    n40,
    n_total,
    CAST(n30 AS FLOAT) / n_total                    AS ratio_30,
    CAST(n40 AS FLOAT) / n_total                    AS ratio_40,
    2.0 * POWER(n30 - n40, 2) / (n_total * 1.0)     AS chi_square,
    -- chi² critical values (df=1): 0.05 -> 3.841 | 0.01 -> 6.635 | 0.001 -> 10.828
    CASE
        WHEN 2.0 * POWER(n30 - n40, 2) / (n_total * 1.0) < 10.828 THEN 'PASS (p >= 0.001)'
        ELSE 'FAIL - potential SRM'
    END AS verdict
FROM counts;
GO

--   VAL-6: Engagement bucket distribution
--   Expected: light ~33%, medium ~34%, heavy ~33% (rough - discrete ties may skew)
PRINT '--- VAL-6: Engagement bucket distribution ---';
SELECT
    engagement_bucket,
    COUNT(*)                                                   AS n_users,
    CAST(COUNT(*) AS FLOAT)
        / (SELECT COUNT(*) FROM cookie_cats.mart_ab_test_base) AS pct
FROM cookie_cats.mart_ab_test_base
GROUP BY engagement_bucket
ORDER BY
    CASE engagement_bucket WHEN 'light' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END;
GO


--   VAL-7: sum_gamerounds distribution vs Phase 2 baseline
--   Expected: mean, median, max should match Phase 2 EDA (minus the 49854 user)

PRINT '--- VAL-7: sum_gamerounds distribution ---';
SELECT
    version,
    COUNT(*)                                                          AS n,
    round(AVG(CAST(sum_gamerounds AS FLOAT)), 2)                                AS mean_rounds,
    MIN(sum_gamerounds)                                               AS min_rounds,
    MAX(sum_gamerounds)                                               AS max_rounds,
    (SELECT DISTINCT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sum_gamerounds)
                                          OVER (PARTITION BY version)
     FROM cookie_cats.mart_ab_test_base m
     WHERE m.version = b.version)                                     AS median_rounds
FROM cookie_cats.mart_ab_test_base b
GROUP BY version;
GO

--   VAL-8: Retention baseline preview

PRINT '--- VAL-8: Retention baseline preview ---';
SELECT
    version,
    COUNT(*)                                     AS n,
    round(AVG(CAST(retention_1 AS FLOAT)), 4)              AS d1_retention_rate,
    round(AVG(CAST(retention_7 AS FLOAT)), 4)              AS d7_retention_rate
FROM cookie_cats.mart_ab_test_base
GROUP BY version;
GO