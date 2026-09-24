-- RetailLab star schema. Python registers three staging frames before this runs:
--   stg_customers (one row per customer, experiment columns included)
--   stg_campaigns (arm, label, contact_cost)
--   stg_sectors   (sector, gross_margin, operating_margin, as_of)

CREATE OR REPLACE TABLE dim_customer AS
SELECT unit_id AS customer_id, history_segment, pre_spend AS history, recency, newbie,
       channel, zip_code
FROM stg_customers;

CREATE OR REPLACE TABLE dim_campaign AS
SELECT arm, label, contact_cost FROM stg_campaigns;

CREATE OR REPLACE TABLE dim_sector_finance AS
SELECT sector, gross_margin, operating_margin, as_of FROM stg_sectors;

CREATE OR REPLACE TABLE fact_exposure AS
SELECT unit_id AS customer_id, arm FROM stg_customers;

CREATE OR REPLACE TABLE fact_sales AS
SELECT unit_id AS customer_id, visit, conversion, revenue FROM stg_customers;

-- Customer grain: exposure, outcome, and pre-period covariate side by side.
CREATE OR REPLACE TABLE mart_experiment AS
SELECT e.customer_id, e.arm, s.visit, s.conversion, s.revenue, c.history AS pre_spend,
       c.history_segment, c.channel, c.zip_code, c.newbie
FROM fact_exposure e
JOIN fact_sales s USING (customer_id)
JOIN dim_customer c USING (customer_id);

-- Arm x sector grain: the same measured lift priced under each sector's margin.
CREATE OR REPLACE TABLE mart_pnl AS
WITH arms AS (
    SELECT arm, COUNT(*) AS customers, AVG(conversion) AS conversion_rate,
           AVG(revenue) AS revenue_per_customer
    FROM mart_experiment
    GROUP BY arm
),
baseline AS (SELECT revenue_per_customer AS control_rpc FROM arms WHERE arm = 'control')
SELECT a.arm, f.sector, a.customers, a.conversion_rate, a.revenue_per_customer,
       (a.revenue_per_customer - b.control_rpc) * a.customers AS incremental_revenue,
       (a.revenue_per_customer - b.control_rpc) * a.customers * f.gross_margin AS gross_profit,
       a.customers * k.contact_cost AS marketing_cost,
       (a.revenue_per_customer - b.control_rpc) * a.customers * f.gross_margin
           - a.customers * k.contact_cost AS contribution
FROM arms a
CROSS JOIN baseline b
JOIN dim_campaign k USING (arm)
CROSS JOIN dim_sector_finance f
WHERE a.arm <> 'control'
ORDER BY a.arm, f.sector;
