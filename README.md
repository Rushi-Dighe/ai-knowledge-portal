# AI Knowledge Portal

An AI-powered, multi-tenant data catalog and analytics assistant for Snowflake. Built entirely with **Cortex Code (Coco)**. Zero manual documentation. Point it at any database — the AI crawls, documents, and lets anyone query it in plain English.

---

## What It Does

1. **Crawls** any database/schema — reads every table, column, and samples data automatically
2. **Enriches** with AI — Cortex LLM writes business descriptions and tags columns as METRIC or DIMENSION
3. **Enables semantic search** — find "revenue" even if no column is named revenue
4. **Answers questions in English** — type "revenue per supplier" and get live SQL results

---

## Architecture

| Object | Type | Purpose |
|--------|------|---------|
| `DATA_LAYER.CORE.AI_CATALOG` | Table | Central metadata store for all cataloged schemas |
| `DATA_LAYER.CORE.DATA_CRAWLER` | Procedure (Python) | Scans any schema, collects columns + sample data |
| `DATA_LAYER.CORE.ENRICH_AI_CATALOG` | Procedure (SQL) | Cortex LLM auto-documents every column |
| `DATA_LAYER.CORE.CATALOG_SEARCH` | Cortex Search Service | Semantic search across all cataloged data |
| `DATA_LAYER.CORE.KNOWLEDGE_PORTAL` | Streamlit App | User-facing portal with 4 tabs |
| `KNOWLEDGE_PORTAL_EMAIL` | Notification Integration | Enables email reports from the portal |

---

## Streamlit App — 4 Tabs

| Tab | What It Does | Backend |
|-----|-------------|---------|
| **Catalog Browser** | Browse tables/columns with AI descriptions, filter by table | Queries `AI_CATALOG` table |
| **KPI Discovery** | Surface all METRIC-tagged columns, toggle current/all sources | Filters `COLUMN_ROLE = 'METRIC'` |
| **Semantic Search** | Meaning-based search across all data (e.g., "revenue" finds PRICE) | Cortex Search Service + vector embeddings |
| **Ask AI** | Plain English → SQL → live results with auto-detected joins | Cortex LLM `llama3.1-70b` + join relationship detection |

Both **KPI Discovery** and **Ask AI** support one-click **email reports**.

---

## Setup — New Snowflake Account (Step by Step)

### Prerequisites

- Snowflake account with **ACCOUNTADMIN** role (or equivalent privileges)
- A warehouse (the scripts use `COMPUTE_WH` — update if yours is different)
- Cortex LLM access enabled on your account

### Step 1: Create Schema

Run `setup/01_create_schema.sql`:

```sql
CREATE DATABASE IF NOT EXISTS DATA_LAYER;
CREATE SCHEMA IF NOT EXISTS DATA_LAYER.CORE;
```

### Step 2: Create Metadata Table

Run `setup/02_create_ai_catalog.sql` — creates the `AI_CATALOG` table that stores all column-level metadata across every cataloged database.

### Step 3: Create Data Crawler

Run `setup/03_create_data_crawler.sql` — creates the `DATA_CRAWLER` Snowpark Python procedure that:
- Scans any `database.schema` via `INFORMATION_SCHEMA.COLUMNS`
- Samples 5 distinct values per column
- Inserts metadata into `AI_CATALOG`

**Usage:**
```sql
CALL DATA_LAYER.CORE.DATA_CRAWLER('MY_DATABASE', 'MY_SCHEMA');
```

### Step 4: Create AI Enrichment

Run `setup/04_create_enrich_ai_catalog.sql` — creates the `ENRICH_AI_CATALOG` procedure that:
- Uses `SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b')` to generate one-sentence descriptions
- Classifies each column as `METRIC` or `DIMENSION`
- Builds `SEARCH_TEXT` for the Cortex Search index

**Usage:**
```sql
CALL DATA_LAYER.CORE.ENRICH_AI_CATALOG('MY_DATABASE', 'MY_SCHEMA');
```

### Step 5: Create Cortex Search Service

Run `setup/05_create_cortex_search.sql` — creates the `CATALOG_SEARCH` service with:
- Semantic search on `SEARCH_TEXT` column
- Filterable by `SOURCE_DATABASE`, `SOURCE_SCHEMA`, `TABLE_NAME`, `COLUMN_ROLE`
- Auto-refreshes every 1 hour

### Step 6: Deploy Streamlit App

Run `setup/06_create_streamlit_app.sql` — creates the stage and Streamlit object.

Then upload `app.py` to the stage:

```sql
-- Option A: From local machine
PUT file://streamlit/app.py @DATA_LAYER.CORE.KNOWLEDGE_PORTAL_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Option B: From a Git repository (if set up)
CREATE OR REPLACE STREAMLIT DATA_LAYER.CORE.KNOWLEDGE_PORTAL
  FROM @YOUR_GIT_REPO/branches/main/streamlit/
  MAIN_FILE = 'app.py'
  QUERY_WAREHOUSE = 'COMPUTE_WH'
  TITLE = 'AI Knowledge Portal';
```

### Step 7: Create Email Integration

Run `setup/07_create_email_integration.sql` — enables the "Email Report" buttons.

**Important:** Email recipients must verify their email in Snowflake:
- Go to **Snowsight → Profile (bottom-left) → Verify Email**

### Step 8: Test End-to-End

```sql
-- Crawl a schema
CALL DATA_LAYER.CORE.DATA_CRAWLER('DATA_LAYER', 'RAW');

-- Enrich with AI
CALL DATA_LAYER.CORE.ENRICH_AI_CATALOG('DATA_LAYER', 'RAW');

-- Verify
SELECT * FROM DATA_LAYER.CORE.AI_CATALOG LIMIT 10;

-- Test search
SELECT PARSE_JSON(
  SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'DATA_LAYER.CORE.CATALOG_SEARCH',
    '{"query": "revenue", "columns": ["TABLE_NAME","COLUMN_NAME","AI_DESCRIPTION"], "limit": 5}'
  )
)['results'] AS results;
```

Then open the Streamlit app from **Projects → Streamlit → AI Knowledge Portal**.

---

## Usage

1. Open the Streamlit app
2. Select any **database** and **schema** from the sidebar
3. If not yet cataloged, click **Crawl & Enrich** (one-click setup)
4. Use the 4 tabs:
   - **Catalog Browser** — understand your data
   - **KPI Discovery** — find all measurable metrics
   - **Semantic Search** — search by meaning, not keywords
   - **Ask AI** — ask questions in English, get SQL + results
5. Click **Email Report** to send results to any verified email

---

## Customization

### Change the warehouse
Update `COMPUTE_WH` in these files:
- `setup/05_create_cortex_search.sql`
- `setup/06_create_streamlit_app.sql`

### Change the LLM model
- Enrichment uses `llama3.1-8b` — edit in `setup/04_create_enrich_ai_catalog.sql`
- SQL generation uses `llama3.1-70b` — edit in `streamlit/app.py` (Ask AI tab)

### Hide internal schemas
The app already hides `INFORMATION_SCHEMA` and `CORE`. To hide more, edit this line in `streamlit/app.py`:
```python
schemas = [r["name"] for r in schemas_rows if r["name"] not in ("INFORMATION_SCHEMA", "CORE")]
```

### Column naming
For best results with Ask AI, ensure source table columns are **UPPERCASE**. If columns are lowercase (e.g., from CSV INFER_SCHEMA), rename them:
```sql
ALTER TABLE MY_DB.MY_SCHEMA.MY_TABLE RENAME COLUMN "lowercase_col" TO UPPERCASE_COL;
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Column descriptions | Cortex LLM — `llama3.1-8b` |
| SQL generation | Cortex LLM — `llama3.1-70b` |
| Semantic search | Cortex Search Service — `snowflake-arctic-embed-m-v1.5` |
| Data crawler | Snowpark Python stored procedure |
| UI | Streamlit in Snowflake |
| Email | `SYSTEM$SEND_EMAIL` notification integration |

---

## Cost

The entire build and operation costs under **6 Snowflake credits**:
- Warehouse compute: ~5.66 credits (data loading, crawling, procedures)
- AI Services (Cortex LLM): ~0.02 credits (enrichment + SQL generation)
- Copy Files: ~0.002 credits

---

## File Structure

```
ai-knowledge-portal/
├── README.md
├── setup/
│   ├── 01_create_schema.sql
│   ├── 02_create_ai_catalog.sql
│   ├── 03_create_data_crawler.sql
│   ├── 04_create_enrich_ai_catalog.sql
│   ├── 05_create_cortex_search.sql
│   ├── 06_create_streamlit_app.sql
│   └── 07_create_email_integration.sql
└── streamlit/
    └── app.py
```

---

## Built With

Built entirely through conversation with **Cortex Code (Coco)** — Snowflake's AI coding assistant. Zero hand-written code.