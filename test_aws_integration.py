#!/usr/bin/env python3
"""
Test script for AWS integration functionality.
This script tests the AWS data fetcher without requiring actual AWS credentials.
"""

import sys
import os
from unittest.mock import Mock, patch
import pytest

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aws_data_fetcher import fetch_ec2_metrics, validate_aws_credentials, get_available_instances

def test_aws_data_fetcher_import():
    """Test that the AWS data fetcher can be imported successfully."""
    try:
        from aws_data_fetcher import fetch_ec2_metrics, validate_aws_credentials, get_available_instances
        print("✓ AWS data fetcher imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import AWS data fetcher: {e}")
        return False

def test_fetch_ec2_metrics_mock():
    """Test the fetch_ec2_metrics function with mocked AWS responses."""
    # Mock instance IDs
    instance_ids = ['i-1234567890abcdef0', 'i-0987654321fedcba0']
    
    # Mock CloudWatch response
    mock_cloudwatch_response = {
        'Datapoints': [
            {'Average': 25.5, 'Timestamp': '2024-01-01T00:00:00Z'},
            {'Average': 30.2, 'Timestamp': '2024-01-01T00:05:00Z'},
            {'Average': 28.1, 'Timestamp': '2024-01-01T00:10:00Z'}
        ]
    }
    
    with patch('boto3.client') as mock_boto3:
        # Configure the mock
        mock_cloudwatch = Mock()
        mock_cloudwatch.get_metric_statistics.return_value = mock_cloudwatch_response
        mock_boto3.return_value = mock_cloudwatch
        
        # Test the function
        result = fetch_ec2_metrics(instance_ids, 'us-east-1', 'test-key', 'test-secret')
        
        # Verify the result
        assert len(result) == 2, f"Expected 2 results, got {len(result)}"
        assert 'cpu' in result[0], "Result should contain 'cpu' key"
        assert 'ram' in result[0], "Result should contain 'ram' key"
        assert 'duration' in result[0], "Result should contain 'duration' key"
        assert 'instance_id' in result[0], "Result should contain 'instance_id' key"
        
        print("✓ fetch_ec2_metrics function works correctly with mocked data")
        return True

def test_validate_aws_credentials_mock():
    """Test the validate_aws_credentials function with mocked AWS responses."""
    with patch('boto3.client') as mock_boto3:
        # Configure the mock for successful validation
        mock_ec2 = Mock()
        mock_ec2.describe_instances.return_value = {'Reservations': []}
        mock_boto3.return_value = mock_ec2
        
        # Test successful validation
        is_valid, message = validate_aws_credentials('test-key', 'test-secret', 'us-east-1')
        assert is_valid == True, f"Expected True, got {is_valid}"
        assert "valid" in message.lower(), f"Expected 'valid' in message, got '{message}'"
        
        print("✓ validate_aws_credentials function works correctly with mocked data")
        return True

def test_get_available_instances_mock():
    """Test the get_available_instances function with mocked AWS responses."""
    # Mock EC2 response
    mock_ec2_response = {
        'Reservations': [
            {
                'Instances': [
                    {'InstanceId': 'i-1234567890abcdef0', 'State': {'Name': 'running'}},
                    {'InstanceId': 'i-0987654321fedcba0', 'State': {'Name': 'stopped'}}
                ]
            }
        ]
    }
    
    with patch('boto3.client') as mock_boto3:
        # Configure the mock
        mock_ec2 = Mock()
        mock_ec2.describe_instances.return_value = mock_ec2_response
        mock_boto3.return_value = mock_ec2
        
        # Test the function
        result = get_available_instances('test-key', 'test-secret', 'us-east-1')
        
        # Verify the result
        assert len(result) == 2, f"Expected 2 instances, got {len(result)}"
        assert 'i-1234567890abcdef0' in result, "Expected instance ID not found"
        assert 'i-0987654321fedcba0' in result, "Expected instance ID not found"
        
        print("✓ get_available_instances function works correctly with mocked data")
        return True

def test_main_import():
    """Test that the main application can be imported with AWS integration."""
    try:
        # This will test if the main.py can be imported with the AWS integration
        from main import EnergySchedulerApp
        print("✓ Main application imported successfully with AWS integration")
        return True
    except ImportError as e:
        print(f"✗ Failed to import main application: {e}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    print("Testing AWS Integration...")
    print("=" * 50)
    
    tests = [
        test_aws_data_fetcher_import,
        test_fetch_ec2_metrics_mock,
        test_validate_aws_credentials_mock,
        test_get_available_instances_mock,
        test_main_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! AWS integration is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 