{{
  config(
    materialized='view',
    tags=['staging', 'bank_marketing']
  )
}}

WITH source AS (
    SELECT * FROM {{ source('raw_data', 'bank_marketing') }}
),

cleaned AS (
    SELECT
        -- Identificadores
        ROW_NUMBER() OVER (ORDER BY age, job, marital) as customer_id,
        
        -- Información demográfica
        CAST(age AS INT64) as age,
        LOWER(TRIM(job)) as job,
        LOWER(TRIM(marital)) as marital,
        LOWER(TRIM(education)) as education,
        
        -- Información financiera
        LOWER(TRIM(default)) as has_default,
        LOWER(TRIM(housing)) as has_housing_loan,
        LOWER(TRIM(loan)) as has_personal_loan,
        
        -- Información de contacto
        LOWER(TRIM(contact)) as contact_type,
        LOWER(TRIM(month)) as month,
        LOWER(TRIM(day_of_week)) as day_of_week,
        
        -- Métricas de campaña
        CAST(duration AS INT64) as call_duration_seconds,
        CAST(campaign AS INT64) as campaign_number,
        CAST(pdays AS INT64) as days_since_last_contact,
        CAST(previous AS INT64) as previous_campaign_contacts,
        LOWER(TRIM(poutcome)) as previous_campaign_outcome,
        
        -- Indicadores económicos
        CAST(emp_var_rate AS FLOAT64) as employment_variation_rate,
        CAST(cons_price_idx AS FLOAT64) as consumer_price_index,
        CAST(cons_conf_idx AS FLOAT64) as consumer_confidence_index,
        CAST(euribor3m AS FLOAT64) as euribor_3m_rate,
        CAST(nr_employed AS FLOAT64) as number_employed,
        
        -- Variable objetivo
        LOWER(TRIM(y)) as subscribed,
        
        -- Metadatos
        CURRENT_TIMESTAMP() as processed_at
        
    FROM source
    WHERE 
        age IS NOT NULL 
        AND age BETWEEN 18 AND 95
        AND job IS NOT NULL
        AND marital IS NOT NULL
        AND education IS NOT NULL
        AND duration >= 0
        AND campaign >= 1
)

SELECT * FROM cleaned
