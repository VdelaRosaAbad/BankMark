#!/usr/bin/env python3
"""
Unit tests for data ingestion script
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Agregar el directorio scripts al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from data_ingestion import BankMarketingDataIngestion

class TestBankMarketingDataIngestion:
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for testing"""
        return pd.DataFrame({
            'age': [25, 30, 35, 40, 45],
            'job': ['admin.', 'technician', 'services', 'management', 'blue-collar'],
            'marital': ['married', 'single', 'married', 'divorced', 'single'],
            'education': ['university.degree', 'high.school', 'basic.9y', 'university.degree', 'basic.6y'],
            'default': ['no', 'no', 'no', 'no', 'no'],
            'housing': ['yes', 'yes', 'no', 'yes', 'no'],
            'loan': ['no', 'no', 'no', 'no', 'no'],
            'contact': ['cellular', 'cellular', 'telephone', 'cellular', 'telephone'],
            'month': ['may', 'jun', 'jul', 'aug', 'sep'],
            'day_of_week': ['mon', 'tue', 'wed', 'thu', 'fri'],
            'duration': [261, 149, 226, 151, 307],
            'campaign': [1, 1, 1, 1, 1],
            'pdays': [-1, -1, -1, -1, -1],
            'previous': [0, 0, 0, 0, 0],
            'poutcome': ['nonexistent', 'nonexistent', 'nonexistent', 'nonexistent', 'nonexistent'],
            'emp.var.rate': [1.1, 1.1, 1.1, 1.1, 1.1],
            'cons.price.idx': [93.994, 93.994, 93.994, 93.994, 93.994],
            'cons.conf.idx': [-36.4, -36.4, -36.4, -36.4, -36.4],
            'euribor3m': [4.857, 4.857, 4.857, 4.857, 4.857],
            'nr.employed': [5191.0, 5191.0, 5191.0, 5191.0, 5191.0],
            'y': ['no', 'no', 'yes', 'no', 'yes']
        })
    
    @pytest.fixture
    def ingestion_instance(self):
        """Create ingestion instance for testing"""
        return BankMarketingDataIngestion(project_id="test-project")
    
    def test_init(self, ingestion_instance):
        """Test initialization"""
        assert ingestion_instance.project_id == "test-project"
        assert ingestion_instance.dataset_id == "raw_data"
        assert ingestion_instance.client is not None
    
    @patch('requests.get')
    def test_download_data_success(self, mock_get, ingestion_instance, sample_data):
        """Test successful data download"""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"fake_zip_content"
        mock_get.return_value = mock_response
        
        # Mock zipfile and pandas
        with patch('zipfile.ZipFile') as mock_zip:
            with patch('pandas.read_csv', return_value=sample_data) as mock_read_csv:
                with patch('builtins.open', create=True):
                    result = ingestion_instance.download_data()
                    
                    assert isinstance(result, pd.DataFrame)
                    assert len(result) == 5
                    assert list(result.columns) == list(sample_data.columns)
    
    @patch('requests.get')
    def test_download_data_failure(self, mock_get, ingestion_instance):
        """Test data download failure"""
        # Mock failed response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Download failed")
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception):
            ingestion_instance.download_data()
    
    def test_validate_data_success(self, ingestion_instance, sample_data):
        """Test successful data validation"""
        result = ingestion_instance.validate_data(sample_data)
        assert result is True
    
    def test_validate_data_missing_columns(self, ingestion_instance, sample_data):
        """Test validation with missing columns"""
        # Remove required column
        invalid_data = sample_data.drop(columns=['age'])
        
        result = ingestion_instance.validate_data(invalid_data)
        assert result is False
    
    def test_validate_data_invalid_age(self, ingestion_instance, sample_data):
        """Test validation with invalid age values"""
        # Add invalid age
        invalid_data = sample_data.copy()
        invalid_data.loc[0, 'age'] = 100  # Invalid age
        
        result = ingestion_instance.validate_data(invalid_data)
        assert result is False
    
    def test_validate_data_negative_duration(self, ingestion_instance, sample_data):
        """Test validation with negative duration"""
        # Add negative duration
        invalid_data = sample_data.copy()
        invalid_data.loc[0, 'duration'] = -10  # Invalid duration
        
        result = ingestion_instance.validate_data(invalid_data)
        assert result is False
    
    def test_validate_data_duplicates(self, ingestion_instance, sample_data):
        """Test validation with duplicate records"""
        # Add duplicate row
        invalid_data = pd.concat([sample_data, sample_data.iloc[0:1]])
        
        result = ingestion_instance.validate_data(invalid_data)
        assert result is False
    
    @patch('google.cloud.bigquery.Client')
    def test_create_dataset_exists(self, mock_client, ingestion_instance):
        """Test dataset creation when dataset already exists"""
        # Mock existing dataset
        mock_client.return_value.get_dataset.return_value = Mock()
        
        ingestion_instance.create_dataset()
        
        # Verify get_dataset was called
        mock_client.return_value.get_dataset.assert_called_once()
    
    @patch('google.cloud.bigquery.Client')
    def test_create_dataset_new(self, mock_client, ingestion_instance):
        """Test dataset creation for new dataset"""
        # Mock dataset not found
        from google.cloud.exceptions import NotFound
        mock_client.return_value.get_dataset.side_effect = NotFound("Dataset not found")
        mock_client.return_value.create_dataset.return_value = Mock()
        
        ingestion_instance.create_dataset()
        
        # Verify create_dataset was called
        mock_client.return_value.create_dataset.assert_called_once()
    
    @patch('google.cloud.bigquery.Client')
    def test_load_to_bigquery_success(self, mock_client, ingestion_instance, sample_data):
        """Test successful BigQuery load"""
        # Mock successful load job
        mock_job = Mock()
        mock_job.result.return_value = None
        mock_client.return_value.load_table_from_dataframe.return_value = mock_job
        
        result = ingestion_instance.load_to_bigquery(sample_data)
        
        assert result is True
        mock_client.return_value.load_table_from_dataframe.assert_called_once()
    
    @patch('google.cloud.bigquery.Client')
    def test_load_to_bigquery_failure(self, mock_client, ingestion_instance, sample_data):
        """Test BigQuery load failure"""
        # Mock failed load job
        mock_client.return_value.load_table_from_dataframe.side_effect = Exception("Load failed")
        
        with pytest.raises(Exception):
            ingestion_instance.load_to_bigquery(sample_data)
    
    @patch('os.path.exists')
    @patch('os.remove')
    @patch('shutil.rmtree')
    def test_cleanup_success(self, mock_rmtree, mock_remove, mock_exists, ingestion_instance):
        """Test successful cleanup"""
        mock_exists.return_value = True
        
        ingestion_instance.cleanup()
        
        mock_remove.assert_called_once()
        mock_rmtree.assert_called_once()
    
    @patch('os.path.exists')
    @patch('os.remove')
    @patch('shutil.rmtree')
    def test_cleanup_files_not_exist(self, mock_rmtree, mock_remove, mock_exists, ingestion_instance):
        """Test cleanup when files don't exist"""
        mock_exists.return_value = False
        
        ingestion_instance.cleanup()
        
        # Should not raise exception
        assert True
    
    @patch.object(BankMarketingDataIngestion, 'download_data')
    @patch.object(BankMarketingDataIngestion, 'validate_data')
    @patch.object(BankMarketingDataIngestion, 'create_dataset')
    @patch.object(BankMarketingDataIngestion, 'load_to_bigquery')
    @patch.object(BankMarketingDataIngestion, 'cleanup')
    def test_run_success(self, mock_cleanup, mock_load, mock_create, mock_validate, mock_download, ingestion_instance, sample_data):
        """Test successful pipeline run"""
        mock_download.return_value = sample_data
        mock_validate.return_value = True
        mock_load.return_value = True
        
        result = ingestion_instance.run()
        
        assert result is True
        mock_download.assert_called_once()
        mock_validate.assert_called_once()
        mock_create.assert_called_once()
        mock_load.assert_called_once()
        mock_cleanup.assert_called_once()
    
    @patch.object(BankMarketingDataIngestion, 'download_data')
    @patch.object(BankMarketingDataIngestion, 'cleanup')
    def test_run_validation_failure(self, mock_cleanup, mock_download, ingestion_instance, sample_data):
        """Test pipeline run with validation failure"""
        mock_download.return_value = sample_data
        
        # Mock validation failure
        with patch.object(ingestion_instance, 'validate_data', return_value=False):
            result = ingestion_instance.run()
            
            assert result is False
            mock_cleanup.assert_called_once()
    
    @patch.object(BankMarketingDataIngestion, 'download_data')
    @patch.object(BankMarketingDataIngestion, 'cleanup')
    def test_run_exception(self, mock_cleanup, mock_download, ingestion_instance):
        """Test pipeline run with exception"""
        mock_download.side_effect = Exception("Test exception")
        
        result = ingestion_instance.run()
        
        assert result is False
        mock_cleanup.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__])
