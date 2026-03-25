-- =============================================================
-- AI Knowledge Portal - Streamlit App Deployment
-- =============================================================
-- Creates the stage and Streamlit app object.
-- After running this, upload app.py to the stage:
--
--   PUT file://path/to/app.py @DATA_LAYER.CORE.KNOWLEDGE_PORTAL_STAGE
--       AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
-- =============================================================

CREATE OR REPLACE STAGE DATA_LAYER.CORE.KNOWLEDGE_PORTAL_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- Upload app.py to stage before running below
-- PUT file://streamlit/app.py @DATA_LAYER.CORE.KNOWLEDGE_PORTAL_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

CREATE OR REPLACE STREAMLIT DATA_LAYER.CORE.KNOWLEDGE_PORTAL
    ROOT_LOCATION = '@DATA_LAYER.CORE.KNOWLEDGE_PORTAL_STAGE'
    MAIN_FILE = 'app.py'
    QUERY_WAREHOUSE = 'COMPUTE_WH'
    TITLE = 'AI Knowledge Portal';
