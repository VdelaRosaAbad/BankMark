#!/usr/bin/env python3
"""
Data Ingestion Script for Bank Marketing Dataset
Downloads data from UCI repository and loads into BigQuery
"""

import pandas as pd
import requests
import logging
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import os
from datetime import datetime
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BankMarketingDataIngestion:
    def __init__(self, project_id="BankMarketingVada", dataset_id="raw_data"):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)
        
    def download_data(self):
        """Download data from UCI repository"""
        try:
            logger.info("Downloading Bank Marketing dataset from UCI...")
            
            # URL del dataset UCI
            url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00222/bank.zip"
            
            # Descargar datos
            response = requests.get(url)
            response.raise_for_status()
            
            # Guardar archivo temporal
            with open("bank.zip", "wb") as f:
                f.write(response.content)
            
            # Extraer y leer datos
            import zipfile
            with zipfile.ZipFile("bank.zip", "r") as zip_ref:
                zip_ref.extractall("temp_data")
            
            # Leer el archivo CSV
            df = pd.read_csv("temp_data/bank-full.csv", sep=";")
            
            logger.info(f"Downloaded {len(df)} records successfully")
            return df
            
        except Exception as e:
            logger.error(f"Error downloading data: {str(e)}")
            raise
    
    def validate_data(self, df):
        """Validate data quality"""
        logger.info("Validating data quality...")
        
        # Mostrar columnas reales encontradas
        logger.info(f"Found columns: {list(df.columns)}")
        
        # Validaciones básicas (más flexibles)
        validations = {
            "total_rows": len(df) > 0,
            "has_age": 'age' in df.columns,
            "has_job": 'job' in df.columns,
            "has_marital": 'marital' in df.columns,
            "has_education": 'education' in df.columns,
            "has_default": 'default' in df.columns,
            "has_housing": 'housing' in df.columns,
            "has_loan": 'loan' in df.columns,
            "has_contact": 'contact' in df.columns,
            "has_month": 'month' in df.columns,
            "has_day_of_week": 'day_of_week' in df.columns,
            "has_duration": 'duration' in df.columns,
            "has_campaign": 'campaign' in df.columns,
            "has_pdays": 'pdays' in df.columns,
            "has_previous": 'previous' in df.columns,
            "has_poutcome": 'poutcome' in df.columns,
            "has_y": 'y' in df.columns,
            "age_range": df['age'].between(18, 95).all() if 'age' in df.columns else True,
            "duration_positive": (df['duration'] >= 0).all() if 'duration' in df.columns else True,
            "campaign_positive": (df['campaign'] >= 1).all() if 'campaign' in df.columns else True,
            "no_duplicates": not df.duplicated().any()
        }
        
        # Verificar validaciones críticas
        critical_validations = [
            "total_rows", "has_age", "has_job", "has_marital", "has_education",
            "has_default", "has_housing", "has_loan", "has_contact", "has_month",
            "has_day_of_week", "has_duration", "has_campaign", "has_pdays",
            "has_previous", "has_poutcome", "has_y"
        ]
        
        failed_critical = [k for k in critical_validations if not validations.get(k, False)]
        
        if failed_critical:
            logger.error(f"Critical validations failed: {failed_critical}")
            return False
        
        # Verificar validaciones opcionales
        optional_validations = ["age_range", "duration_positive", "campaign_positive", "no_duplicates"]
        failed_optional = [k for k in optional_validations if not validations.get(k, False)]
        
        if failed_optional:
            logger.warning(f"Optional validations failed: {failed_optional}")
        
        logger.info("Data validation passed")
        return True
    
    def create_dataset(self):
        """Create BigQuery dataset if it doesn't exist"""
        try:
            dataset_ref = self.client.dataset(self.dataset_id)
            self.client.get_dataset(dataset_ref)
            logger.info(f"Dataset {self.dataset_id} already exists")
        except NotFound:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            dataset = self.client.create_dataset(dataset)
            logger.info(f"Created dataset {self.dataset_id}")
    
    def load_to_bigquery(self, df):
        """Load data to BigQuery"""
        try:
            logger.info("Loading data to BigQuery...")
            
            # Preparar datos para BigQuery
            table_id = f"{self.project_id}.{self.dataset_id}.bank_marketing"
            
            # Crear schema dinámicamente basado en las columnas reales
            schema = []
            for col in df.columns:
                if col in ['age', 'duration', 'campaign', 'pdays', 'previous']:
                    schema.append(bigquery.SchemaField(col, "INTEGER"))
                elif col in ['emp.var.rate', 'cons.price.idx', 'cons.conf.idx', 'euribor3m', 'nr.employed']:
                    schema.append(bigquery.SchemaField(col, "FLOAT"))
                else:
                    schema.append(bigquery.SchemaField(col, "STRING"))
            
            # Configurar job
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                schema=schema
            )
            
            # Cargar datos
            job = self.client.load_table_from_dataframe(
                df, table_id, job_config=job_config
            )
            job.result()  # Esperar a que termine
            
            logger.info(f"Successfully loaded {len(df)} rows to {table_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading to BigQuery: {str(e)}")
            raise
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        try:
            if os.path.exists("bank.zip"):
                os.remove("bank.zip")
            if os.path.exists("temp_data"):
                shutil.rmtree("temp_data")
            logger.info("Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup warning: {str(e)}")
    
    def run(self):
        """Execute complete ingestion pipeline"""
        try:
            logger.info("Starting Bank Marketing data ingestion...")
            
            # 1. Descargar datos
            df = self.download_data()
            
            # 2. Validar datos
            if not self.validate_data(df):
                raise ValueError("Data validation failed")
            
            # 3. Crear dataset
            self.create_dataset()
            
            # 4. Cargar a BigQuery
            self.load_to_bigquery(df)
            
            # 5. Limpiar archivos temporales
            self.cleanup()
            
            logger.info("Data ingestion completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Data ingestion failed: {str(e)}")
            self.cleanup()
            return False

def main():
    """Main function"""
    try:
        # Configurar proyecto desde variables de entorno
        project_id = os.getenv("GCP_PROJECT_ID", "BankMarketingVada")
        
        # Ejecutar ingesta
        ingestion = BankMarketingDataIngestion(project_id=project_id)
        success = ingestion.run()
        
        if success:
            print("✅ Data ingestion completed successfully!")
            sys.exit(0)
        else:
            print("❌ Data ingestion failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
