-- =============================================================
-- AI Knowledge Portal - AI_CATALOG Table
-- =============================================================
-- Central metadata store for all cataloged databases/schemas.
-- Each row = one column from a source table, enriched with
-- AI-generated descriptions and METRIC/DIMENSION classification.
-- =============================================================

CREATE OR REPLACE TABLE DATA_LAYER.CORE.AI_CATALOG (
    CATALOG_ID       VARCHAR DEFAULT UUID_STRING(),
    SOURCE_DATABASE  VARCHAR,
    SOURCE_SCHEMA    VARCHAR,
    TABLE_NAME       VARCHAR,
    COLUMN_NAME      VARCHAR,
    DATA_TYPE        VARCHAR,
    ORDINAL_POSITION NUMBER,
    IS_NULLABLE      VARCHAR,
    SAMPLE_VALUES    VARCHAR,
    AI_DESCRIPTION   VARCHAR,
    COLUMN_ROLE      VARCHAR DEFAULT 'DIMENSION',
    SEARCH_TEXT      VARCHAR,
    CRAWLED_AT       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    ENRICHED_AT      TIMESTAMP_NTZ,
    PRIMARY KEY (SOURCE_DATABASE, SOURCE_SCHEMA, TABLE_NAME, COLUMN_NAME)
);
