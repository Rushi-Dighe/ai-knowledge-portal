CONTEXT: WHAT WE'RE BUILDING AND WHY
============================================================

PROBLEM STATEMENT:
Every organization has dozens of databases and schemas in Snowflake, but nobody 
knows what the data actually means. New analysts join and spend weeks figuring 
out which tables to use. Business users can't self-serve because they don't know 
which column is "revenue" vs "amount" vs "total_price". There's no single place 
to search across all your data assets and ask plain English questions like 
"show me revenue by region."

Today, data documentation is manual, outdated, and lives in scattered wikis. 
Data teams waste 30-40% of their time just finding and understanding data 
before they can analyze it.

THE SOLUTION — "AI Knowledge Portal":
We're building a fully automated, AI-powered data catalog and analytics assistant 
that works across ANY database in a Snowflake account. No manual documentation needed.

Here's how it works:
1. CRAWL — A procedure scans any database.schema, reads every table's columns 
   and grabs sample data automatically.
2. ENRICH — AI (Cortex LLM) reads each column name + sample data and writes a 
   business-friendly description. It also tags columns that look like KPIs 
   (revenue, quantity, cost, etc.) as METRIC.
3. SEARCH — A Cortex Search Service enables semantic search across all cataloged 
   data so users can search "revenue" and find relevant columns across all databases.
4. ASK — A Streamlit app lets users ask ANY question in plain English 
   (e.g., "revenue per supplier", "top customers by order count"). The AI reads 
   the full schema context and generates executable SQL on the fly. Users can 
   preview results with one click.

This is MULTI-TENANT — one portal serves all databases. Select a database, 
select a schema, and either browse the catalog or ask questions. If a schema 
hasn't been crawled yet, one click crawls and enriches it.

The key innovation: ZERO manual setup per database. Point it at any schema, 
the AI understands your data, documents it, and lets anyone query it in English.

ARCHITECTURE:
- DATA_LAYER.CORE.AI_CATALOG → Central metadata store (all tenants)
- DATA_LAYER.CORE.DATA_CRAWLER → Snowpark procedure to scan any schema
- DATA_LAYER.CORE.ENRICH_AI_CATALOG → Cortex LLM auto-documents every column
- DATA_LAYER.CORE.CATALOG_SEARCH → Cortex Search Service for semantic search
- DATA_LAYER.CORE.KNOWLEDGE_PORTAL → Streamlit app (the user-facing portal)

Now build it. Follow every step below in exact order. Test each step before 
moving to the next. Do not skip anything.
