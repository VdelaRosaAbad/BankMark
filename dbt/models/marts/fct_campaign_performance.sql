{{
  config(
    materialized='table',
    tags=['marts', 'kpis', 'campaign_performance']
  )
}}

WITH campaign_data AS (
    SELECT * FROM {{ ref('int_customer_segments') }}
),

daily_performance AS (
    SELECT
        DATE(processed_at) as campaign_date,
        campaign_number,
        age_group,
        job_category,
        income_level,
        credit_risk_profile,
        customer_engagement_level,
        call_duration_category,
        
        -- Métricas de volumen
        COUNT(*) as total_contacts,
        COUNT(DISTINCT customer_id) as unique_customers,
        
        -- Métricas de conversión
        COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) as successful_contacts,
        COUNT(CASE WHEN subscribed = 'no' THEN 1 END) as unsuccessful_contacts,
        
        -- Tasa de conversión
        ROUND(
            COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) * 100.0 / COUNT(*), 
            2
        ) as conversion_rate,
        
        -- Métricas de duración
        AVG(call_duration_seconds) as avg_call_duration,
        SUM(call_duration_seconds) as total_call_duration,
        
        -- Métricas de eficiencia
        ROUND(
            COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) * 100.0 / NULLIF(SUM(call_duration_seconds), 0), 
            4
        ) as conversion_per_minute,
        
        -- Metadatos
        CURRENT_TIMESTAMP() as last_updated
        
    FROM campaign_data
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
),

campaign_summary AS (
    SELECT
        campaign_number,
        campaign_date,
        
        -- KPIs principales
        SUM(total_contacts) as total_contacts,
        SUM(successful_contacts) as total_conversions,
        ROUND(
            SUM(successful_contacts) * 100.0 / SUM(total_contacts), 
            2
        ) as overall_conversion_rate,
        
        -- Métricas de eficiencia
        AVG(avg_call_duration) as avg_call_duration,
        SUM(total_call_duration) as total_call_duration_hours,
        
        -- Segmentación por edad
        SUM(CASE WHEN age_group = 'Young (18-24)' THEN successful_contacts ELSE 0 END) as young_conversions,
        SUM(CASE WHEN age_group = 'Young Adult (25-34)' THEN successful_contacts ELSE 0 END) as young_adult_conversions,
        SUM(CASE WHEN age_group = 'Adult (35-44)' THEN successful_contacts ELSE 0 END) as adult_conversions,
        SUM(CASE WHEN age_group = 'Middle Age (45-54)' THEN successful_contacts ELSE 0 END) as middle_age_conversions,
        SUM(CASE WHEN age_group = 'Senior (55-64)' THEN successful_contacts ELSE 0 END) as senior_conversions,
        SUM(CASE WHEN age_group = 'Elder (65+)' THEN successful_contacts ELSE 0 END) as elder_conversions,
        
        -- Segmentación por ocupación
        SUM(CASE WHEN job_category = 'Professional' THEN successful_contacts ELSE 0 END) as professional_conversions,
        SUM(CASE WHEN job_category = 'Skilled' THEN successful_contacts ELSE 0 END) as skilled_conversions,
        SUM(CASE WHEN job_category = 'Manual' THEN successful_contacts ELSE 0 END) as manual_conversions,
        SUM(CASE WHEN job_category = 'Student/Retired' THEN successful_contacts ELSE 0 END) as student_retired_conversions,
        
        -- Segmentación por riesgo crediticio
        SUM(CASE WHEN credit_risk_profile = 'Low Risk' THEN successful_contacts ELSE 0 END) as low_risk_conversions,
        SUM(CASE WHEN credit_risk_profile = 'Medium Risk' THEN successful_contacts ELSE 0 END) as medium_risk_conversions,
        SUM(CASE WHEN credit_risk_profile = 'High Risk' THEN successful_contacts ELSE 0 END) as high_risk_conversions,
        
        -- Metadatos
        MAX(last_updated) as last_updated
        
    FROM daily_performance
    GROUP BY 1, 2
)

SELECT 
    *,
    -- KPIs calculados adicionales
    CASE 
        WHEN overall_conversion_rate >= 15 THEN 'Excellent'
        WHEN overall_conversion_rate >= 10 THEN 'Good'
        WHEN overall_conversion_rate >= 5 THEN 'Average'
        ELSE 'Poor'
    END as performance_category,
    
    -- Eficiencia por hora de llamada
    ROUND(
        total_conversions * 3600.0 / NULLIF(total_call_duration_hours, 0), 
        2
    ) as conversions_per_hour,
    
    -- Tendencias (comparación con campaña anterior)
    LAG(overall_conversion_rate) OVER (
        PARTITION BY campaign_number 
        ORDER BY campaign_date
    ) as previous_conversion_rate,
    
    -- Cambio en tasa de conversión
    ROUND(
        overall_conversion_rate - LAG(overall_conversion_rate) OVER (
            PARTITION BY campaign_number 
            ORDER BY campaign_date
        ), 
        2
    ) as conversion_rate_change
    
FROM campaign_summary
ORDER BY campaign_number, campaign_date
