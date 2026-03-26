-- =============================================================
-- AI Knowledge Portal - Email Notification Integration
-- =============================================================
-- Enables the portal to send KPI reports and query results
-- via email using SYSTEM$SEND_EMAIL.
--
-- IMPORTANT: Recipients must have verified email addresses
-- in Snowflake. Go to Snowsight > Profile > Verify Email.
-- =============================================================

CREATE OR REPLACE NOTIFICATION INTEGRATION KNOWLEDGE_PORTAL_EMAIL
  TYPE = EMAIL
  ENABLED = TRUE;
