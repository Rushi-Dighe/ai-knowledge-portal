-- =============================================================
-- AI Knowledge Portal - Cortex Search Service
-- =============================================================
-- Enables semantic (meaning-based) search across all cataloged
-- data. Powered by snowflake-arctic-embed vector embeddings.
--
-- Supports filtering by SOURCE_DATABASE, SOURCE_SCHEMA,
-- TABLE_NAME, and COLUMN_ROLE.
-- =============================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE DATA_LAYER.CORE.CATALOG_SEARCH
    ON SEARCH_TEXT
    ATTRIBUTES SOURCE_DATABASE, SOURCE_SCHEMA, TABLE_NAME, COLUMN_ROLE
    WAREHOUSE = COMPUTE_WH
    TARGET_LAG = '1 hour'
AS (
    SELECT
        SEARCH_TEXT,
        SOURCE_DATABASE,
        SOURCE_SCHEMA,
        TABLE_NAME,
        COLUMN_NAME,
        DATA_TYPE,
        AI_DESCRIPTION,
        COLUMN_ROLE,
        SAMPLE_VALUES
    FROM DATA_LAYER.CORE.AI_CATALOG
);
