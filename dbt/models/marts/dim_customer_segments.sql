{{
  config(
    materialized='table',
    tags=['marts', 'dimensions', 'customer_segments']
  )
}}

WITH customer_data AS (
    SELECT * FROM {{ ref('int_customer_segments') }}
),

segment_metrics AS (
    SELECT
        age_group,
        age_category,
        job_category,
        income_level,
        credit_risk_profile,
        customer_engagement_level,
        call_duration_category,
        
        -- Métricas por segmento
        COUNT(*) as segment_size,
        COUNT(DISTINCT customer_id) as unique_customers,
        
        -- Conversiones por segmento
        COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) as segment_conversions,
        COUNT(CASE WHEN subscribed = 'no' THEN 1 END) as segment_non_conversions,
        
        -- Tasa de conversión por segmento
        ROUND(
            COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) * 100.0 / COUNT(*), 
            2
        ) as segment_conversion_rate,
        
        -- Métricas de duración por segmento
        AVG(call_duration_seconds) as avg_call_duration_segment,
        SUM(call_duration_seconds) as total_call_duration_segment,
        
        -- Eficiencia por segmento
        ROUND(
            COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) * 100.0 / NULLIF(SUM(call_duration_seconds), 0), 
            4
        ) as segment_conversion_per_minute,
        
        -- Metadatos
        CURRENT_TIMESTAMP() as last_updated
        
    FROM customer_data
    GROUP BY 1, 2, 3, 4, 5, 6, 7
),

age_segment_analysis AS (
    SELECT
        age_group,
        age_category,
        COUNT(*) as age_segment_size,
        COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) as age_conversions,
        ROUND(
            COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) * 100.0 / COUNT(*), 
            2
        ) as age_conversion_rate,
        AVG(call_duration_seconds) as avg_age_call_duration
    FROM customer_data
    GROUP BY 1, 2
),

job_segment_analysis AS (
    SELECT
        job_category,
        income_level,
        COUNT(*) as job_segment_size,
        COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) as job_conversions,
        ROUND(
            COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) * 100.0 / COUNT(*), 
            2
        ) as job_conversion_rate,
        AVG(call_duration_seconds) as avg_job_call_duration
    FROM customer_data
    GROUP BY 1, 2
),

risk_segment_analysis AS (
    SELECT
        credit_risk_profile,
        COUNT(*) as risk_segment_size,
        COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) as risk_conversions,
        ROUND(
            COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) * 100.0 / COUNT(*), 
            2
        ) as risk_conversion_rate,
        AVG(call_duration_seconds) as avg_risk_call_duration
    FROM customer_data
    GROUP BY 1
),

engagement_analysis AS (
    SELECT
        customer_engagement_level,
        COUNT(*) as engagement_segment_size,
        COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) as engagement_conversions,
        ROUND(
            COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) * 100.0 / COUNT(*), 
            2
        ) as engagement_conversion_rate,
        AVG(call_duration_seconds) as avg_engagement_call_duration
    FROM customer_data
    GROUP BY 1
)

SELECT 
    sm.*,
    
    -- Análisis por edad
    asa.age_conversion_rate as age_segment_conversion_rate,
    asa.avg_age_call_duration,
    
    -- Análisis por ocupación
    jsa.job_conversion_rate as job_segment_conversion_rate,
    jsa.avg_job_call_duration,
    
    -- Análisis por riesgo
    rsa.risk_conversion_rate as risk_segment_conversion_rate,
    rsa.avg_risk_call_duration,
    
    -- Análisis por engagement
    ea.engagement_conversion_rate as engagement_segment_conversion_rate,
    ea.avg_engagement_call_duration,
    
    -- KPIs calculados
    CASE 
        WHEN sm.segment_conversion_rate >= 15 THEN 'High Performer'
        WHEN sm.segment_conversion_rate >= 10 THEN 'Medium Performer'
        WHEN sm.segment_conversion_rate >= 5 THEN 'Low Performer'
        ELSE 'Underperformer'
    END as segment_performance_category,
    
    -- Eficiencia del segmento
    ROUND(
        sm.segment_conversions * 3600.0 / NULLIF(sm.total_call_duration_segment, 0), 
        2
    ) as segment_conversions_per_hour,
    
    -- Tamaño relativo del segmento
    ROUND(
        sm.segment_size * 100.0 / SUM(sm.segment_size) OVER (), 
        2
    ) as segment_size_percentage
    
FROM segment_metrics sm
LEFT JOIN age_segment_analysis asa ON sm.age_group = asa.age_group
LEFT JOIN job_segment_analysis jsa ON sm.job_category = jsa.job_category
LEFT JOIN risk_segment_analysis rsa ON sm.credit_risk_profile = rsa.credit_risk_profile
LEFT JOIN engagement_analysis ea ON sm.customer_engagement_level = ea.customer_engagement_level
ORDER BY sm.segment_conversion_rate DESC
