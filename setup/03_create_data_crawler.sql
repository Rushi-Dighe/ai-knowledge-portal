-- =============================================================
-- AI Knowledge Portal - DATA_CRAWLER Procedure
-- =============================================================
-- Scans any database.schema using INFORMATION_SCHEMA, collects
-- column metadata and sample values, loads into AI_CATALOG.
--
-- Usage: CALL DATA_LAYER.CORE.DATA_CRAWLER('MY_DB', 'MY_SCHEMA');
-- =============================================================

CREATE OR REPLACE PROCEDURE DATA_LAYER.CORE.DATA_CRAWLER(
    DB_NAME VARCHAR,
    SCHEMA_NAME VARCHAR
)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run'
EXECUTE AS CALLER
AS
$$
def run(session, db_name, schema_name):
    db = db_name.upper()
    sch = schema_name.upper()

    session.sql(f"""
        DELETE FROM DATA_LAYER.CORE.AI_CATALOG
        WHERE SOURCE_DATABASE = '{db}' AND SOURCE_SCHEMA = '{sch}'
    """).collect()

    cols = session.sql(f"""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, ORDINAL_POSITION, IS_NULLABLE
        FROM {db}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{sch}'
        ORDER BY TABLE_NAME, ORDINAL_POSITION
    """).collect()

    tables_seen = {}
    for c in cols:
        tbl = c['TABLE_NAME']
        col_name = c['COLUMN_NAME']
        dtype = c['DATA_TYPE']
        ordinal = c['ORDINAL_POSITION']
        nullable = c['IS_NULLABLE']

        sample_vals = ''
        try:
            if tbl not in tables_seen:
                tables_seen[tbl] = True
            safe_col = f'"{col_name}"'
            rows = session.sql(f"""
                SELECT DISTINCT {safe_col}::VARCHAR AS val
                FROM {db}.{sch}."{tbl}"
                WHERE {safe_col} IS NOT NULL
                LIMIT 5
            """).collect()
            sample_vals = ', '.join([str(r['VAL']) for r in rows if r['VAL']])
        except:
            sample_vals = ''

        sample_escaped = sample_vals.replace("'", "''")
        col_escaped = col_name.replace("'", "''")
        tbl_escaped = tbl.replace("'", "''")

        session.sql(f"""
            INSERT INTO DATA_LAYER.CORE.AI_CATALOG
                (SOURCE_DATABASE, SOURCE_SCHEMA, TABLE_NAME, COLUMN_NAME,
                 DATA_TYPE, ORDINAL_POSITION, IS_NULLABLE, SAMPLE_VALUES, CRAWLED_AT)
            VALUES ('{db}', '{sch}', '{tbl_escaped}', '{col_escaped}',
                    '{dtype}', {ordinal}, '{nullable}', '{sample_escaped}', CURRENT_TIMESTAMP())
        """).collect()

    return f'Crawled {len(cols)} columns from {db}.{sch}'
$$;
