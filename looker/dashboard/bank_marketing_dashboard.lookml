# Bank Marketing Analytics Dashboard
# LookML configuration for Bank Marketing KPIs and Analytics

connection: "bank_marketing_bigquery"

# Dimension Groups
dimension_group: created {
  sql: ${TABLE}.processed_at ;;
  timeframes: [
    raw,
    time,
    date,
    week,
    month,
    quarter,
    year
  ]
  type: time
}

# Dimensions
dimension: customer_id {
  primary_key: yes
  sql: ${TABLE}.customer_id ;;
  type: number
}

dimension: age {
  sql: ${TABLE}.age ;;
  type: number
}

dimension: age_group {
  sql: ${TABLE}.age_group ;;
  type: string
}

dimension: job {
  sql: ${TABLE}.job ;;
  type: string
}

dimension: job_category {
  sql: ${TABLE}.job_category ;;
  type: string
}

dimension: marital {
  sql: ${TABLE}.marital ;;
  type: string
}

dimension: education {
  sql: ${TABLE}.education ;;
  type: string
}

dimension: subscribed {
  sql: ${TABLE}.subscribed ;;
  type: string
}

dimension: campaign_number {
  sql: ${TABLE}.campaign_number ;;
  type: number
}

dimension: call_duration_seconds {
  sql: ${TABLE}.call_duration_seconds ;;
  type: number
}

dimension: call_duration_category {
  sql: ${TABLE}.call_duration_category ;;
  type: string
}

dimension: income_level {
  sql: ${TABLE}.income_level ;;
  type: string
}

dimension: credit_risk_profile {
  sql: ${TABLE}.credit_risk_profile ;;
  type: string
}

dimension: customer_engagement_level {
  sql: ${TABLE}.customer_engagement_level ;;
  type: string
}

# Measures
measure: total_contacts {
  sql: COUNT(*) ;;
  type: count
}

measure: successful_contacts {
  sql: COUNT(CASE WHEN ${subscribed} = 'yes' THEN 1 END) ;;
  type: count
}

measure: conversion_rate {
  sql: ${successful_contacts} * 100.0 / NULLIF(${total_contacts}, 0) ;;
  type: number
  value_format_name: percent_2
}

measure: avg_call_duration {
  sql: AVG(${call_duration_seconds}) ;;
  type: average
  value_format_name: decimal_1
}

measure: total_call_duration_hours {
  sql: SUM(${call_duration_seconds}) / 3600.0 ;;
  type: sum
  value_format_name: decimal_2
}

measure: unique_customers {
  sql: COUNT(DISTINCT ${customer_id}) ;;
  type: count
}

# KPIs específicos
measure: young_conversions {
  sql: COUNT(CASE WHEN ${subscribed} = 'yes' AND ${age_group} = 'Young (18-24)' THEN 1 END) ;;
  type: count
}

measure: professional_conversions {
  sql: COUNT(CASE WHEN ${subscribed} = 'yes' AND ${job_category} = 'Professional' THEN 1 END) ;;
  type: count
}

measure: low_risk_conversions {
  sql: COUNT(CASE WHEN ${subscribed} = 'yes' AND ${credit_risk_profile} = 'Low Risk' THEN 1 END) ;;
  type: count
}

# Modelo principal
explore: stg_bank_marketing {
  label: "Bank Marketing Raw Data"
  description: "Raw data from UCI Bank Marketing dataset"
  
  # Filtros recomendados
  always_filter: {
    filters: [created_date: "30 days"]
  }
}

# Modelo de segmentación
explore: int_customer_segments {
  label: "Customer Segmentation"
  description: "Customer segmentation and analysis"
  
  # Filtros recomendados
  always_filter: {
    filters: [created_date: "30 days"]
  }
}

# Modelo de rendimiento de campañas
explore: fct_campaign_performance {
  label: "Campaign Performance"
  description: "Campaign performance KPIs and metrics"
  
  # Filtros recomendados
  always_filter: {
    filters: [campaign_date: "30 days"]
  }
}

# Modelo de segmentación dimensional
explore: dim_customer_segments {
  label: "Customer Segments Analysis"
  description: "Detailed customer segment analysis"
  
  # Filtros recomendados
  always_filter: {
    filters: [last_updated: "30 days"]
  }
}

# Dashboard Configuration
dashboard: bank_marketing_analytics {
  title: "Bank Marketing Analytics Dashboard"
  description: "Comprehensive analytics for bank marketing campaigns"
  
  # Filtros del dashboard
  filters: [
    {
      name: "Date Range"
      type: "date_filter"
      default_value: "30 days"
    },
    {
      name: "Campaign"
      type: "field_filter"
      field: "campaign_number"
    },
    {
      name: "Age Group"
      type: "field_filter"
      field: "age_group"
    },
    {
      name: "Job Category"
      type: "field_filter"
      field: "job_category"
    },
    {
      name: "Credit Risk"
      type: "field_filter"
      field: "credit_risk_profile"
    }
  ]
  
  # Elementos del dashboard
  elements: [
    {
      title: "Conversion Rate Overview"
      type: "vis"
      query: {
        model: "fct_campaign_performance"
        fields: ["campaign_number", "overall_conversion_rate", "total_contacts", "total_conversions"]
        filters: [{field: "campaign_date", value: "30 days"}]
        sorts: ["campaign_number"]
      }
      chart_type: "line"
    },
    {
      title: "Customer Segmentation"
      type: "vis"
      query: {
        model: "dim_customer_segments"
        fields: ["age_group", "job_category", "segment_conversion_rate", "segment_size"]
        filters: [{field: "last_updated", value: "30 days"}]
        sorts: ["segment_conversion_rate desc"]
        limit: 20
      }
      chart_type: "heatmap"
    },
    {
      title: "Campaign Performance by Age"
      type: "vis"
      query: {
        model: "fct_campaign_performance"
        fields: ["age_group", "young_conversions", "young_adult_conversions", "adult_conversions", "middle_age_conversions", "senior_conversions", "elder_conversions"]
        filters: [{field: "campaign_date", value: "30 days"}]
      }
      chart_type: "bar"
    },
    {
      title: "Job Category Performance"
      type: "vis"
      query: {
        model: "fct_campaign_performance"
        fields: ["job_category", "professional_conversions", "skilled_conversions", "manual_conversions", "student_retired_conversions"]
        filters: [{field: "campaign_date", value: "30 days"}]
      }
      chart_type: "bar"
    },
    {
      title: "Credit Risk Analysis"
      type: "vis"
      query: {
        model: "fct_campaign_performance"
        fields: ["credit_risk_profile", "low_risk_conversions", "medium_risk_conversions", "high_risk_conversions"]
        filters: [{field: "campaign_date", value: "30 days"}]
      }
      chart_type: "pie"
    },
    {
      title: "Call Duration Analysis"
      type: "vis"
      query: {
        model: "int_customer_segments"
        fields: ["call_duration_category", "COUNT(*)", "conversion_rate"]
        filters: [{field: "processed_at", value: "30 days"}]
      }
      chart_type: "scatter"
    },
    {
      title: "Daily Conversion Trends"
      type: "vis"
      query: {
        model: "fct_campaign_performance"
        fields: ["campaign_date", "overall_conversion_rate", "total_conversions"]
        filters: [{field: "campaign_date", value: "30 days"}]
        sorts: ["campaign_date"]
      }
      chart_type: "line"
    },
    {
      title: "Performance Summary"
      type: "text"
      content: |
        ## Key Performance Indicators
        
        **Overall Conversion Rate**: {{ fct_campaign_performance.overall_conversion_rate }}
        **Total Contacts**: {{ fct_campaign_performance.total_contacts }}
        **Successful Contacts**: {{ fct_campaign_performance.total_conversions }}
        **Average Call Duration**: {{ fct_campaign_performance.avg_call_duration }} seconds
        
        **Top Performing Segments**:
        - Age Group: {{ dim_customer_segments.age_group }}
        - Job Category: {{ dim_customer_segments.job_category }}
        - Conversion Rate: {{ dim_customer_segments.segment_conversion_rate }}
    ]
}
