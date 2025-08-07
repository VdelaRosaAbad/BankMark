{{
  config(
    materialized='view',
    tags=['intermediate', 'customer_segments']
  )
}}

WITH customer_data AS (
    SELECT * FROM {{ ref('stg_bank_marketing') }}
),

age_segments AS (
    SELECT
        customer_id,
        age,
        CASE 
            WHEN age < 25 THEN 'Young (18-24)'
            WHEN age BETWEEN 25 AND 34 THEN 'Young Adult (25-34)'
            WHEN age BETWEEN 35 AND 44 THEN 'Adult (35-44)'
            WHEN age BETWEEN 45 AND 54 THEN 'Middle Age (45-54)'
            WHEN age BETWEEN 55 AND 64 THEN 'Senior (55-64)'
            ELSE 'Elder (65+)'
        END as age_group,
        
        CASE 
            WHEN age < 30 THEN 'Young'
            WHEN age BETWEEN 30 AND 50 THEN 'Middle'
            ELSE 'Senior'
        END as age_category
    FROM customer_data
),

job_categories AS (
    SELECT
        customer_id,
        job,
        CASE 
            WHEN job IN ('admin.', 'management', 'executive') THEN 'Professional'
            WHEN job IN ('technician', 'services', 'entrepreneur') THEN 'Skilled'
            WHEN job IN ('blue-collar', 'housemaid', 'unemployed') THEN 'Manual'
            WHEN job IN ('student', 'retired') THEN 'Student/Retired'
            ELSE 'Other'
        END as job_category,
        
        CASE 
            WHEN job IN ('admin.', 'management', 'executive', 'technician') THEN 'High Income'
            WHEN job IN ('services', 'entrepreneur', 'blue-collar') THEN 'Medium Income'
            ELSE 'Low Income'
        END as income_level
    FROM customer_data
),

financial_profile AS (
    SELECT
        customer_id,
        has_default,
        has_housing_loan,
        has_personal_loan,
        CASE 
            WHEN has_default = 'yes' OR has_housing_loan = 'yes' OR has_personal_loan = 'yes' THEN 'High Risk'
            WHEN has_housing_loan = 'yes' OR has_personal_loan = 'yes' THEN 'Medium Risk'
            ELSE 'Low Risk'
        END as credit_risk_profile
    FROM customer_data
),

campaign_history AS (
    SELECT
        customer_id,
        campaign_number,
        previous_campaign_contacts,
        previous_campaign_outcome,
        CASE 
            WHEN previous_campaign_contacts = 0 THEN 'New Customer'
            WHEN previous_campaign_contacts BETWEEN 1 AND 3 THEN 'Occasional'
            WHEN previous_campaign_contacts BETWEEN 4 AND 10 THEN 'Regular'
            ELSE 'Frequent'
        END as customer_engagement_level,
        
        CASE 
            WHEN previous_campaign_outcome = 'success' THEN 'Previous Success'
            WHEN previous_campaign_outcome = 'failure' THEN 'Previous Failure'
            WHEN previous_campaign_outcome = 'other' THEN 'Previous Other'
            ELSE 'No Previous Contact'
        END as previous_outcome_category
    FROM customer_data
)

SELECT 
    cd.customer_id,
    cd.age,
    cd.job,
    cd.marital,
    cd.education,
    cd.subscribed,
    cd.call_duration_seconds,
    cd.campaign_number,
    cd.processed_at,
    
    -- Segmentaciones
    ag.age_group,
    ag.age_category,
    jc.job_category,
    jc.income_level,
    fp.credit_risk_profile,
    ch.customer_engagement_level,
    ch.previous_outcome_category,
    
    -- Métricas calculadas
    CASE 
        WHEN cd.subscribed = 'yes' THEN 1 
        ELSE 0 
    END as is_converted,
    
    CASE 
        WHEN cd.call_duration_seconds > 300 THEN 'Long Call'
        WHEN cd.call_duration_seconds > 120 THEN 'Medium Call'
        ELSE 'Short Call'
    END as call_duration_category
    
FROM customer_data cd
LEFT JOIN age_segments ag ON cd.customer_id = ag.customer_id
LEFT JOIN job_categories jc ON cd.customer_id = jc.customer_id
LEFT JOIN financial_profile fp ON cd.customer_id = fp.customer_id
LEFT JOIN campaign_history ch ON cd.customer_id = ch.customer_id
