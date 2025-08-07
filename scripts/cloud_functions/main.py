#!/usr/bin/env python3
"""
Cloud Function for Bank Marketing Analytics Automation
Handles daily pipeline execution and notifications
"""

import functions_framework
import requests
import json
import logging
from datetime import datetime, timedelta
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.http
def bank_marketing_trigger(request):
    """HTTP Cloud Function trigger for daily pipeline execution"""
    
    try:
        logger.info("Starting Bank Marketing daily pipeline...")
        
        # Configuración
        project_id = os.getenv("GCP_PROJECT_ID", "BankMarketingVada")
        github_token = os.getenv("GITHUB_TOKEN")
        workflow_id = "ci-cd-pipeline.yml"
        
        # Trigger GitHub Actions workflow
        if github_token:
            trigger_github_workflow(github_token, workflow_id)
        
        # Ejecutar pipeline local si es necesario
        execute_local_pipeline()
        
        # Enviar notificación
        send_notification("Pipeline executed successfully")
        
        return {
            "status": "success",
            "message": "Bank Marketing pipeline executed successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        send_notification(f"Pipeline failed: {str(e)}")
        
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }, 500

def trigger_github_workflow(token, workflow_id):
    """Trigger GitHub Actions workflow"""
    try:
        url = f"https://api.github.com/repos/VdelaRosaAbad/BankMark/actions/workflows/{workflow_id}/dispatches"
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "ref": "main",
            "inputs": {
                "trigger": "scheduled"
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        logger.info("GitHub Actions workflow triggered successfully")
        
    except Exception as e:
        logger.error(f"Failed to trigger GitHub workflow: {str(e)}")
        raise

def execute_local_pipeline():
    """Execute pipeline locally if needed"""
    try:
        # Aquí se ejecutarían los comandos del pipeline
        # En una implementación real, esto se haría con subprocess
        
        logger.info("Local pipeline execution completed")
        
    except Exception as e:
        logger.error(f"Local pipeline execution failed: {str(e)}")
        raise

def send_notification(message):
    """Send notification via email or Slack"""
    try:
        # Configuración de notificación
        notification_type = os.getenv("NOTIFICATION_TYPE", "email")
        
        if notification_type == "email":
            send_email_notification(message)
        elif notification_type == "slack":
            send_slack_notification(message)
        
        logger.info(f"Notification sent: {message}")
        
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")

def send_email_notification(message):
    """Send email notification"""
    # Implementación de envío de email
    # Usar la misma lógica que en email_notifications.py
    pass

def send_slack_notification(message):
    """Send Slack notification"""
    try:
        webhook_url = os.getenv("SLACK_WEBHOOK")
        if webhook_url:
            payload = {
                "text": f"Bank Marketing Pipeline: {message}",
                "username": "Bank Marketing Bot",
                "icon_emoji": ":bank:"
            }
            
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")

@functions_framework.http
def send_daily_report(request):
    """HTTP Cloud Function for sending daily reports"""
    
    try:
        logger.info("Generating and sending daily report...")
        
        # Importar y ejecutar el script de notificaciones
        from email_notifications import BankMarketingEmailNotifier
        
        notifier = BankMarketingEmailNotifier()
        success = notifier.run()
        
        if success:
            return {
                "status": "success",
                "message": "Daily report sent successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "Failed to send daily report",
                "timestamp": datetime.now().isoformat()
            }, 500
            
    except Exception as e:
        logger.error(f"Daily report failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }, 500

@functions_framework.http
def data_quality_check(request):
    """HTTP Cloud Function for data quality checks"""
    
    try:
        logger.info("Running data quality checks...")
        
        # Importar y ejecutar el script de calidad
        from quality_checks import BankMarketingQualityChecker
        
        checker = BankMarketingQualityChecker()
        report = checker.run()
        
        # Enviar alerta si la calidad es baja
        if report['quality_score'] < 95:
            send_notification(f"Data quality alert: {report['quality_score']}%")
        
        return {
            "status": "success",
            "quality_score": report['quality_score'],
            "message": "Data quality check completed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Data quality check failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }, 500

@functions_framework.http
def kpi_calculation(request):
    """HTTP Cloud Function for KPI calculations"""
    
    try:
        logger.info("Calculating KPIs...")
        
        from google.cloud import bigquery
        import pandas as pd
        
        # Configuración
        project_id = os.getenv("GCP_PROJECT_ID", "BankMarketingVada")
        client = bigquery.Client(project=project_id)
        
        # Query para KPIs principales
        kpi_query = """
        SELECT 
            DATE(processed_at) as report_date,
            COUNT(*) as total_contacts,
            COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) as successful_contacts,
            ROUND(COUNT(CASE WHEN subscribed = 'yes' THEN 1 END) * 100.0 / COUNT(*), 2) as conversion_rate,
            AVG(call_duration_seconds) as avg_call_duration
        FROM `BankMarketingVada.bank_marketing.stg_bank_marketing`
        WHERE DATE(processed_at) = CURRENT_DATE() - 1
        """
        
        # Ejecutar query
        df = client.query(kpi_query).to_dataframe()
        
        if not df.empty:
            kpis = df.iloc[0].to_dict()
            
            # Enviar KPIs por email si están por debajo del umbral
            if kpis['conversion_rate'] < 5.0:
                send_notification(f"Low conversion rate alert: {kpis['conversion_rate']}%")
            
            return {
                "status": "success",
                "kpis": kpis,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "warning",
                "message": "No data found for yesterday",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"KPI calculation failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }, 500

if __name__ == "__main__":
    # Para pruebas locales
    print("Bank Marketing Cloud Functions")
    print("Available functions:")
    print("- bank_marketing_trigger")
    print("- send_daily_report")
    print("- data_quality_check")
    print("- kpi_calculation")
