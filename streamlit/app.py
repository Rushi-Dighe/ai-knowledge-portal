import streamlit as st
from snowflake.snowpark.context import get_active_session
import json

session = get_active_session()

st.set_page_config(page_title="AI Knowledge Portal", layout="wide")

def send_email_report(subject, html_body, recipient):
    safe_subject = subject.replace("'", "''")
    safe_body = html_body.replace("'", "''")
    safe_email = recipient.replace("'", "''")
    session.sql(
        f"CALL SYSTEM$SEND_EMAIL('KNOWLEDGE_PORTAL_EMAIL', '{safe_email}', '{safe_subject}', '{safe_body}', 'text/html')"
    ).collect()

def df_to_html_table(df):
    header = "".join([f"<th style='padding:8px;border:1px solid #ddd;background:#f2f2f2;text-align:left'>{c}</th>" for c in df.columns])
    rows = ""
    for _, row in df.head(50).iterrows():
        cells = "".join([f"<td style='padding:8px;border:1px solid #ddd'>{row[c]}</td>" for c in df.columns])
        rows += f"<tr>{cells}</tr>"
    return f"<table style='border-collapse:collapse;width:100%;font-family:Arial,sans-serif'><tr>{header}</tr>{rows}</table>"

st.sidebar.title("AI Knowledge Portal")
st.sidebar.markdown("---")

cataloged = session.sql(
    "SELECT SOURCE_DATABASE, SOURCE_SCHEMA, COUNT(*) AS COLS, "
    "SUM(CASE WHEN COLUMN_ROLE = 'METRIC' THEN 1 ELSE 0 END) AS KPIS, "
    "COUNT(DISTINCT TABLE_NAME) AS TBLS "
    "FROM DATA_LAYER.CORE.AI_CATALOG GROUP BY 1,2 ORDER BY 1,2"
).to_pandas()

if len(cataloged) > 0:
    st.sidebar.subheader("Cataloged Sources")
    for _, row in cataloged.iterrows():
        st.sidebar.markdown(
            f"**{row['SOURCE_DATABASE']}.{row['SOURCE_SCHEMA']}** — "
            f"{int(row['TBLS'])} tables, {int(row['KPIS'])} KPIs"
        )
else:
    st.sidebar.info("No schemas cataloged yet, Select a source below to get started.")

st.sidebar.markdown("---")

databases = [r["name"] for r in session.sql("SHOW DATABASES").collect()
             if r["name"] not in ("SNOWFLAKE",)]
selected_db = st.sidebar.selectbox("Database", databases,
    index=databases.index("DATA_LAYER") if "DATA_LAYER" in databases else 0)

schemas_rows = session.sql(f"SHOW SCHEMAS IN DATABASE {selected_db}").collect()
schemas = [r["name"] for r in schemas_rows if r["name"] not in ("INFORMATION_SCHEMA", "CORE")]
selected_schema = st.sidebar.selectbox("Schema", schemas)

crawled = session.sql(
    f"SELECT COUNT(*) AS CNT FROM DATA_LAYER.CORE.AI_CATALOG "
    f"WHERE SOURCE_DATABASE = '{selected_db}' AND SOURCE_SCHEMA = '{selected_schema}'"
).collect()[0]["CNT"]

if crawled == 0:
    st.sidebar.warning("Not yet cataloged")
    if st.sidebar.button("Crawl & Enrich", type="primary"):
        with st.spinner(f"Crawling {selected_db}.{selected_schema}..."):
            session.sql(f"CALL DATA_LAYER.CORE.DATA_CRAWLER('{selected_db}', '{selected_schema}')").collect()
        with st.spinner("Enriching with AI..."):
            session.sql(f"CALL DATA_LAYER.CORE.ENRICH_AI_CATALOG('{selected_db}', '{selected_schema}')").collect()
        st.success(f"Cataloged {selected_db}.{selected_schema}! Please refresh the page.")
        st.stop()
else:
    st.sidebar.success(f"{crawled} columns cataloged")
    if st.sidebar.button("Re-crawl & Re-enrich"):
        with st.spinner(f"Re-crawling {selected_db}.{selected_schema}..."):
            session.sql(f"CALL DATA_LAYER.CORE.DATA_CRAWLER('{selected_db}', '{selected_schema}')").collect()
        with st.spinner("Re-enriching with AI..."):
            session.sql(f"CALL DATA_LAYER.CORE.ENRICH_AI_CATALOG('{selected_db}', '{selected_schema}')").collect()
        st.success("Re-cataloged! Please refresh the page.")
        st.stop()

st.title(f"{selected_db}.{selected_schema}")

if crawled == 0:
    st.info("Select a database and schema from the sidebar, then click **Crawl & Enrich** to get started.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["Catalog Browser", "KPI Discovery", "Semantic Search", "Ask AI"])

with tab1:
    catalog_df = session.sql(
        f"SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_ROLE, AI_DESCRIPTION "
        f"FROM DATA_LAYER.CORE.AI_CATALOG "
        f"WHERE SOURCE_DATABASE = '{selected_db}' AND SOURCE_SCHEMA = '{selected_schema}' "
        f"ORDER BY TABLE_NAME, ORDINAL_POSITION"
    ).to_pandas()
    tables = sorted(catalog_df["TABLE_NAME"].unique())
    selected_table = st.selectbox("Filter by table", ["All Tables"] + list(tables))
    if selected_table != "All Tables":
        catalog_df = catalog_df[catalog_df["TABLE_NAME"] == selected_table]
    st.dataframe(catalog_df, use_container_width=True)
    metric_count = len(catalog_df[catalog_df["COLUMN_ROLE"] == "METRIC"])
    dim_count = len(catalog_df[catalog_df["COLUMN_ROLE"] == "DIMENSION"])
    m1, m2, m3 = st.columns(3)
    m1.metric("Tables", len(tables))
    m2.metric("Metrics", metric_count)
    m3.metric("Dimensions", dim_count)

with tab2:
    scope = st.radio("Scope", ["Current schema only", "All cataloged sources"], horizontal=True)
    if scope == "Current schema only":
        kpi_df = session.sql(
            f"SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, AI_DESCRIPTION, SAMPLE_VALUES "
            f"FROM DATA_LAYER.CORE.AI_CATALOG "
            f"WHERE SOURCE_DATABASE = '{selected_db}' AND SOURCE_SCHEMA = '{selected_schema}' "
            f"AND COLUMN_ROLE = 'METRIC' ORDER BY TABLE_NAME"
        ).to_pandas()
    else:
        kpi_df = session.sql(
            "SELECT SOURCE_DATABASE, SOURCE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, "
            "AI_DESCRIPTION, SAMPLE_VALUES "
            "FROM DATA_LAYER.CORE.AI_CATALOG "
            "WHERE COLUMN_ROLE = 'METRIC' ORDER BY SOURCE_DATABASE, SOURCE_SCHEMA, TABLE_NAME"
        ).to_pandas()

    if len(kpi_df) == 0:
        st.info("No KPIs/metrics found.")
    else:
        st.markdown(f"**{len(kpi_df)} KPIs/metrics found**")
        st.dataframe(kpi_df, use_container_width=True)

        kpi_email = st.text_input("Email address", placeholder="you@company.com", key="kpi_email")
        if st.button("Email KPI Report", key="kpi_email_btn"):
            if kpi_email:
                with st.spinner("Sending..."):
                    try:
                        scope_label = f"{selected_db}.{selected_schema}" if scope == "Current schema only" else "All Sources"
                        html = (
                            f"<h2>KPI Report — {scope_label}</h2>"
                            f"<p>{len(kpi_df)} KPIs/metrics found</p>"
                            + df_to_html_table(kpi_df)
                            + "<br><p style='color:gray;font-size:12px'>Sent from AI Knowledge Portal</p>"
                        )
                        send_email_report(f"KPI Report: {scope_label}", html, kpi_email)
                        st.success(f"Report sent to {kpi_email}!")
                    except Exception as e:
                        st.error(f"Email error: {e}")
            else:
                st.warning("Please enter an email address.")

with tab3:
    search_scope = st.radio("Search scope", ["Current schema", "All cataloged data"], horizontal=True, key="search_scope")
    search_query = st.text_input("Search", placeholder="e.g. revenue, customer name, shipping date...")
    if search_query:
        safe_q = search_query.replace('"', "").replace("\\", "").replace("'", "")
        payload = {
            "query": safe_q,
            "columns": ["TABLE_NAME", "COLUMN_NAME", "AI_DESCRIPTION", "COLUMN_ROLE",
                         "DATA_TYPE", "SOURCE_DATABASE", "SOURCE_SCHEMA"],
            "limit": 10
        }
        if search_scope == "Current schema":
            payload["filter"] = {
                "@and": [
                    {"@eq": {"SOURCE_DATABASE": selected_db}},
                    {"@eq": {"SOURCE_SCHEMA": selected_schema}}
                ]
            }
        search_payload = json.dumps(payload).replace("'", "''")
        search_sql = (
            f"SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW("
            f"'DATA_LAYER.CORE.CATALOG_SEARCH', '{search_payload}'))['results'] AS results"
        )
        try:
            search_result = session.sql(search_sql).collect()[0]["RESULTS"]
            results = json.loads(search_result)
            if results:
                for r in results:
                    role_icon = "M" if r.get("COLUMN_ROLE") == "METRIC" else "D"
                    source = f"{r.get('SOURCE_DATABASE','')}.{r.get('SOURCE_SCHEMA','')}" if search_scope != "Current schema" else ""
                    prefix = f"_{source}_ " if source else ""
                    st.markdown(f"**[{role_icon}] {r['TABLE_NAME']}.{r['COLUMN_NAME']}** (`{r.get('DATA_TYPE', '')}`) {prefix}")
                    st.caption(r.get("AI_DESCRIPTION", ""))
            else:
                st.info("No results found.")
        except Exception as e:
            st.error(f"Search error: {e}")

with tab4:
    table_rows = session.sql(
        f"SELECT TABLE_NAME, "
        f"LISTAGG(COLUMN_NAME || ' ' || DATA_TYPE || ' -- ' || COLUMN_ROLE || ': ' || COALESCE(AI_DESCRIPTION, ''), ', ') "
        f"WITHIN GROUP (ORDER BY ORDINAL_POSITION) AS COLUMNS "
        f"FROM DATA_LAYER.CORE.AI_CATALOG "
        f"WHERE SOURCE_DATABASE = '{selected_db}' AND SOURCE_SCHEMA = '{selected_schema}' "
        f"GROUP BY TABLE_NAME ORDER BY TABLE_NAME"
    ).collect()
    schema_lines = []
    for t in table_rows:
        schema_lines.append(f"TABLE {selected_db}.{selected_schema}.{t['TABLE_NAME']} ({t['COLUMNS']})")
    schema_context = "\n".join(schema_lines)

    col_rows = session.sql(
        f"SELECT TABLE_NAME, COLUMN_NAME FROM DATA_LAYER.CORE.AI_CATALOG "
        f"WHERE SOURCE_DATABASE = '{selected_db}' AND SOURCE_SCHEMA = '{selected_schema}'"
    ).to_pandas()
    table_cols = {}
    for _, r in col_rows.iterrows():
        table_cols.setdefault(r["TABLE_NAME"], set()).add(r["COLUMN_NAME"])
    join_hints = []
    table_names = list(table_cols.keys())
    for i in range(len(table_names)):
        for j in range(i + 1, len(table_names)):
            shared = table_cols[table_names[i]] & table_cols[table_names[j]]
            for col in shared:
                join_hints.append(f"{table_names[i]}.{col} = {table_names[j]}.{col}")
    join_context = "\n".join(join_hints) if join_hints else "No shared columns detected."

    user_question = st.text_input("Ask anything about this data...",
        placeholder="e.g. revenue per supplier, top customers by order count")
    ask_button = st.button("Ask", type="primary")

    if ask_button and user_question:
        with st.spinner("Thinking..."):
            prompt_text = (
                "You are a Snowflake SQL expert. Write a SQL query against the ACTUAL DATA TABLES below.\n"
                "NEVER query DATA_LAYER.CORE.AI_CATALOG or any metadata/catalog table.\n\n"
                "CRITICAL RULES:\n"
                f"- All tables are in {selected_db}.{selected_schema}. Always use fully qualified names.\n"
                "- Column names are UPPERCASE. Do NOT use double quotes around column names.\n"
                "- Return ONLY the SQL query. No explanation, no markdown.\n"
                "- Use the JOIN RELATIONSHIPS below to determine valid join paths. ONLY join tables on columns listed here.\n"
                "- If two tables do not share a column directly, find an intermediate table that connects them.\n\n"
                f"TABLES AND COLUMNS:\n{schema_context}\n\n"
                f"JOIN RELATIONSHIPS (shared column names between tables):\n{join_context}\n\n"
                f"Question: {user_question}\n\nSQL:"
            )
            safe_prompt = prompt_text.replace("'", "''")
            sql_response = session.sql(
                f"SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', '{safe_prompt}') AS SQL_TEXT"
            ).collect()[0]["SQL_TEXT"]
            sql_clean = sql_response.strip()
            if sql_clean.startswith("```"):
                lines = sql_clean.split("\n")
                sql_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else sql_clean
            sql_clean = sql_clean.strip("`").strip()
            if sql_clean.upper().startswith("SQL"):
                sql_clean = sql_clean[3:].strip().lstrip(":").strip()
            st.subheader("Generated SQL")
            st.code(sql_clean, language="sql")
            try:
                result_df = session.sql(sql_clean).to_pandas()
                st.subheader("Results")
                st.dataframe(result_df, use_container_width=True)
                st.session_state["last_result"] = result_df
                st.session_state["last_sql"] = sql_clean
                st.session_state["last_question"] = user_question
            except Exception as e:
                st.error(f"Query error: {e}")

    if "last_result" in st.session_state and st.session_state["last_result"] is not None:
        ai_email = st.text_input("Email address", placeholder="you@company.com", key="ai_email")
        if st.button("Email This Report", key="ai_email_btn"):
            if ai_email:
                with st.spinner("Sending..."):
                    try:
                        q = st.session_state.get("last_question", "Query Results")
                        sql_used = st.session_state.get("last_sql", "")
                        html = (
                            f"<h2>AI Knowledge Portal — Query Results</h2>"
                            f"<p><b>Question:</b> {q}</p>"
                            f"<p><b>Source:</b> {selected_db}.{selected_schema}</p>"
                            f"<pre style='background:#f5f5f5;padding:10px;border-radius:4px'>{sql_used}</pre>"
                            + df_to_html_table(st.session_state['last_result'])
                            + "<br><p style='color:gray;font-size:12px'>Sent from AI Knowledge Portal</p>"
                        )
                        send_email_report(f"AI Query: {q}", html, ai_email)
                        st.success(f"Report sent to {ai_email}!")
                    except Exception as e:
                        st.error(f"Email error: {e}")
            else:
                st.warning("Please enter an email address.")
