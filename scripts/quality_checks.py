#!/usr/bin/env python3
"""
Data Quality Checks for Bank Marketing Dataset
Validates data quality and generates reports
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
import logging
from datetime import datetime
import sys
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BankMarketingQualityChecker:
    def __init__(self, project_id="BankMarketingVada"):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.results = []
    
    def check_data_types(self, df):
        """Check data types are correct"""
        logger.info("Checking data types...")
        
        expected_types = {
            'age': 'int64',
            'job': 'object',
            'marital': 'object',
            'education': 'object',
            'default': 'object',
            'housing': 'object',
            'loan': 'object',
            'contact': 'object',
            'month': 'object',
            'day_of_week': 'object',
            'duration': 'int64',
            'campaign': 'int64',
            'pdays': 'int64',
            'previous': 'int64',
            'poutcome': 'object',
            'emp_var_rate': 'float64',
            'cons_price_idx': 'float64',
            'cons_conf_idx': 'float64',
            'euribor3m': 'float64',
            'nr_employed': 'float64',
            'y': 'object'
        }
        
        issues = []
        for col, expected_type in expected_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if actual_type != expected_type:
                    issues.append(f"Column {col}: expected {expected_type}, got {actual_type}")
        
        self.results.append({
            'test_name': 'Data Types Check',
            'status': 'PASSED' if not issues else 'FAILED',
            'issues': issues,
            'details': f"Checked {len(expected_types)} columns"
        })
        
        return len(issues) == 0
    
    def check_null_values(self, df):
        """Check for null values in required fields"""
        logger.info("Checking null values...")
        
        required_fields = ['age', 'job', 'marital', 'education', 'duration', 'campaign', 'y']
        issues = []
        
        for field in required_fields:
            if field in df.columns:
                null_count = df[field].isnull().sum()
                if null_count > 0:
                    issues.append(f"Field {field}: {null_count} null values")
        
        self.results.append({
            'test_name': 'Null Values Check',
            'status': 'PASSED' if not issues else 'FAILED',
            'issues': issues,
            'details': f"Checked {len(required_fields)} required fields"
        })
        
        return len(issues) == 0
    
    def check_value_ranges(self, df):
        """Check value ranges for numeric fields"""
        logger.info("Checking value ranges...")
        
        range_checks = {
            'age': (18, 95),
            'duration': (0, 5000),
            'campaign': (1, 100),
            'pdays': (-1, 1000),
            'previous': (0, 10)
        }
        
        issues = []
        for field, (min_val, max_val) in range_checks.items():
            if field in df.columns:
                out_of_range = df[field][(df[field] < min_val) | (df[field] > max_val)]
                if len(out_of_range) > 0:
                    issues.append(f"Field {field}: {len(out_of_range)} values outside range [{min_val}, {max_val}]")
        
        self.results.append({
            'test_name': 'Value Ranges Check',
            'status': 'PASSED' if not issues else 'FAILED',
            'issues': issues,
            'details': f"Checked {len(range_checks)} numeric fields"
        })
        
        return len(issues) == 0
    
    def check_accepted_values(self, df):
        """Check categorical fields have accepted values"""
        logger.info("Checking accepted values...")
        
        accepted_values = {
            'job': ['admin.', 'blue-collar', 'entrepreneur', 'housemaid', 'management', 
                   'retired', 'self-employed', 'services', 'student', 'technician', 'unemployed', 'unknown'],
            'marital': ['divorced', 'married', 'single', 'unknown'],
            'education': ['basic.4y', 'basic.6y', 'basic.9y', 'high.school', 'illiterate', 
                         'professional.course', 'university.degree', 'unknown'],
            'default': ['no', 'unknown', 'yes'],
            'housing': ['no', 'unknown', 'yes'],
            'loan': ['no', 'unknown', 'yes'],
            'contact': ['cellular', 'telephone'],
            'month': ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'],
            'day_of_week': ['mon', 'tue', 'wed', 'thu', 'fri'],
            'poutcome': ['failure', 'nonexistent', 'success'],
            'y': ['no', 'yes']
        }
        
        issues = []
        for field, accepted in accepted_values.items():
            if field in df.columns:
                invalid_values = df[field][~df[field].isin(accepted)]
                if len(invalid_values) > 0:
                    unique_invalid = invalid_values.unique()
                    issues.append(f"Field {field}: {len(invalid_values)} invalid values: {unique_invalid}")
        
        self.results.append({
            'test_name': 'Accepted Values Check',
            'status': 'PASSED' if not issues else 'FAILED',
            'issues': issues,
            'details': f"Checked {len(accepted_values)} categorical fields"
        })
        
        return len(issues) == 0
    
    def check_duplicates(self, df):
        """Check for duplicate records"""
        logger.info("Checking for duplicates...")
        
        duplicate_count = df.duplicated().sum()
        
        self.results.append({
            'test_name': 'Duplicate Records Check',
            'status': 'PASSED' if duplicate_count == 0 else 'FAILED',
            'issues': [f"Found {duplicate_count} duplicate records"] if duplicate_count > 0 else [],
            'details': f"Total records: {len(df)}"
        })
        
        return duplicate_count == 0
    
    def check_data_consistency(self, df):
        """Check data consistency rules"""
        logger.info("Checking data consistency...")
        
        issues = []
        
        # Regla 1: Si pdays = -1, previous debe ser 0
        if 'pdays' in df.columns and 'previous' in df.columns:
            inconsistent = df[(df['pdays'] == -1) & (df['previous'] > 0)]
            if len(inconsistent) > 0:
                issues.append(f"Found {len(inconsistent)} records where pdays=-1 but previous>0")
        
        # Regla 2: Si previous = 0, poutcome debe ser 'nonexistent'
        if 'previous' in df.columns and 'poutcome' in df.columns:
            inconsistent = df[(df['previous'] == 0) & (df['poutcome'] != 'nonexistent')]
            if len(inconsistent) > 0:
                issues.append(f"Found {len(inconsistent)} records where previous=0 but poutcome!='nonexistent'")
        
        # Regla 3: Duración debe ser positiva
        if 'duration' in df.columns:
            negative_duration = df[df['duration'] <= 0]
            if len(negative_duration) > 0:
                issues.append(f"Found {len(negative_duration)} records with non-positive duration")
        
        self.results.append({
            'test_name': 'Data Consistency Check',
            'status': 'PASSED' if not issues else 'FAILED',
            'issues': issues,
            'details': "Checked business logic consistency"
        })
        
        return len(issues) == 0
    
    def get_data_from_bigquery(self):
        """Get data from BigQuery for quality checks"""
        try:
            logger.info("Fetching data from BigQuery...")
            
            query = """
            SELECT * FROM `BankMarketingVada.raw_data.bank_marketing`
            LIMIT 10000
            """
            
            df = self.client.query(query).to_dataframe()
            logger.info(f"Retrieved {len(df)} records from BigQuery")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data from BigQuery: {str(e)}")
            raise
    
    def generate_quality_report(self):
        """Generate quality report"""
        logger.info("Generating quality report...")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['status'] == 'PASSED')
        failed_tests = total_tests - passed_tests
        
        quality_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'quality_score': quality_score,
            'results': self.results
        }
        
        logger.info(f"Quality Score: {quality_score:.1f}% ({passed_tests}/{total_tests} tests passed)")
        return report
    
    def run(self):
        """Execute complete quality check pipeline"""
        try:
            logger.info("Starting data quality checks...")
            
            # 1. Obtener datos
            df = self.get_data_from_bigquery()
            
            # 2. Ejecutar verificaciones
            self.check_data_types(df)
            self.check_null_values(df)
            self.check_value_ranges(df)
            self.check_accepted_values(df)
            self.check_duplicates(df)
            self.check_data_consistency(df)
            
            # 3. Generar reporte
            report = self.generate_quality_report()
            
            logger.info("Data quality checks completed successfully!")
            return report
            
        except Exception as e:
            logger.error(f"Data quality checks failed: {str(e)}")
            raise

def main():
    """Main function"""
    try:
        # Configurar proyecto desde variables de entorno
        project_id = os.getenv("GCP_PROJECT_ID", "BankMarketingVada")
        
        # Ejecutar verificaciones de calidad
        checker = BankMarketingQualityChecker(project_id=project_id)
        report = checker.run()
        
        # Mostrar resultados
        print(f"✅ Data Quality Report Generated!")
        print(f"Quality Score: {report['quality_score']:.1f}%")
        print(f"Tests Passed: {report['passed_tests']}/{report['total_tests']}")
        
        if report['failed_tests'] > 0:
            print("⚠️  Some tests failed:")
            for result in report['results']:
                if result['status'] == 'FAILED':
                    print(f"  - {result['test_name']}: {', '.join(result['issues'])}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error in quality checks: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
