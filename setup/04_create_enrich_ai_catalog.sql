-- =============================================================
-- AI Knowledge Portal - ENRICH_AI_CATALOG Procedure
-- =============================================================
-- Uses Cortex LLM (llama3.1-8b) to:
--   1. Generate business-friendly descriptions for each column
--   2. Classify columns as METRIC or DIMENSION
--   3. Build SEARCH_TEXT for Cortex Search indexing
--
-- Usage: CALL DATA_LAYER.CORE.ENRICH_AI_CATALOG('MY_DB', 'MY_SCHEMA');
-- =============================================================

CREATE OR REPLACE PROCEDURE DATA_LAYER.CORE.ENRICH_AI_CATALOG(
    DB_NAME VARCHAR,
    SCHEMA_NAME VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
BEGIN
    UPDATE DATA_LAYER.CORE.AI_CATALOG
    SET AI_DESCRIPTION = SNOWFLAKE.CORTEX.COMPLETE(
            'llama3.1-8b',
            'You are a data catalog assistant. Given the following column metadata, write a concise one-sentence business description. '
            || 'Table: ' || TABLE_NAME
            || ', Column: ' || COLUMN_NAME
            || ', Type: ' || DATA_TYPE
            || ', Samples: ' || COALESCE(SAMPLE_VALUES, 'N/A')
            || '. Reply ONLY with the description, nothing else.'
        ),
        COLUMN_ROLE = CASE
            WHEN SNOWFLAKE.CORTEX.COMPLETE(
                'llama3.1-8b',
                'Is this column a measurable KPI/metric (like revenue, cost, quantity, amount, price, count, total, weight, discount, tax, profit, rate, score)? '
                || 'Column: ' || COLUMN_NAME || ', Type: ' || DATA_TYPE || ', Samples: ' || COALESCE(SAMPLE_VALUES, 'N/A')
                || '. Answer ONLY "METRIC" or "DIMENSION".'
            ) ILIKE '%METRIC%' THEN 'METRIC'
            ELSE 'DIMENSION'
        END,
        SEARCH_TEXT = TABLE_NAME || ' | ' || COLUMN_NAME || ' | ' || DATA_TYPE || ' | ' || COALESCE(SAMPLE_VALUES, ''),
        ENRICHED_AT = CURRENT_TIMESTAMP()
    WHERE SOURCE_DATABASE = UPPER(:DB_NAME)
      AND SOURCE_SCHEMA = UPPER(:SCHEMA_NAME)
      AND AI_DESCRIPTION IS NULL;

    UPDATE DATA_LAYER.CORE.AI_CATALOG
    SET SEARCH_TEXT = TABLE_NAME || ' | ' || COLUMN_NAME || ' | ' || DATA_TYPE
            || ' | ' || COALESCE(AI_DESCRIPTION, '')
            || ' | ' || COALESCE(SAMPLE_VALUES, '')
            || ' | ' || COLUMN_ROLE
    WHERE SOURCE_DATABASE = UPPER(:DB_NAME)
      AND SOURCE_SCHEMA = UPPER(:SCHEMA_NAME);

    RETURN 'Enrichment complete for ' || :DB_NAME || '.' || :SCHEMA_NAME;
END;
