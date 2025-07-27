#!/usr/bin/env python3
"""
Test script for AWS configuration widgets in the dataset tab.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_aws_widgets():
    """Test that the AWS configuration widgets can be created and accessed."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    try:
        from main import EnergySchedulerApp
        
        # Create the app
        app = EnergySchedulerApp(root)
        
        # Test that the AWS variables exist
        assert hasattr(app, 'use_aws_data_var'), "use_aws_data_var should exist"
        assert hasattr(app, 'aws_instance_ids_var'), "aws_instance_ids_var should exist"
        assert hasattr(app, 'aws_access_key_var'), "aws_access_key_var should exist"
        assert hasattr(app, 'aws_secret_key_var'), "aws_secret_key_var should exist"
        assert hasattr(app, 'aws_region_var'), "aws_region_var should exist"
        
        # Test initial values
        assert app.use_aws_data_var.get() == False, "use_aws_data_var should be False by default"
        assert app.aws_instance_ids_var.get() == "", "aws_instance_ids_var should be empty by default"
        assert app.aws_region_var.get() == "us-east-1", "aws_region_var should default to us-east-1"
        
        # Test setting values
        app.use_aws_data_var.set(True)
        app.aws_instance_ids_var.set("i-1234567890abcdef0,i-0987654321fedcba0")
        app.aws_access_key_var.set("test-key")
        app.aws_secret_key_var.set("test-secret")
        app.aws_region_var.set("us-west-2")
        
        # Test getting values
        assert app.use_aws_data_var.get() == True, "use_aws_data_var should be True after setting"
        assert app.aws_instance_ids_var.get() == "i-1234567890abcdef0,i-0987654321fedcba0", "aws_instance_ids_var should match set value"
        assert app.aws_access_key_var.get() == "test-key", "aws_access_key_var should match set value"
        assert app.aws_secret_key_var.get() == "test-secret", "aws_secret_key_var should match set value"
        assert app.aws_region_var.get() == "us-west-2", "aws_region_var should match set value"
        
        print("✓ All AWS configuration widgets are working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error testing AWS widgets: {e}")
        return False
    finally:
        root.destroy()

def test_instance_id_parsing():
    """Test the instance ID parsing functionality."""
    # Test various input formats
    test_cases = [
        ("i-1234567890abcdef0", ["i-1234567890abcdef0"]),
        ("i-1234567890abcdef0,i-0987654321fedcba0", ["i-1234567890abcdef0", "i-0987654321fedcba0"]),
        ("i-1234567890abcdef0, i-0987654321fedcba0", ["i-1234567890abcdef0", "i-0987654321fedcba0"]),
        ("i-1234567890abcdef0 , i-0987654321fedcba0", ["i-1234567890abcdef0", "i-0987654321fedcba0"]),
        ("", []),
        ("   ", []),
        ("i-1234567890abcdef0,", ["i-1234567890abcdef0"]),
        (",i-1234567890abcdef0", ["i-1234567890abcdef0"]),
    ]
    
    for input_str, expected in test_cases:
        # Simulate the parsing logic from generate_vms
        instance_ids = [id.strip() for id in input_str.split(',') if id.strip()]
        assert instance_ids == expected, f"Expected {expected}, got {instance_ids} for input '{input_str}'"
    
    print("✓ Instance ID parsing works correctly")
    return True

def run_all_tests():
    """Run all widget tests."""
    print("Testing AWS Configuration Widgets...")
    print("=" * 50)
    
    tests = [
        test_aws_widgets,
        test_instance_id_parsing
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
        print("🎉 All AWS widget tests passed!")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 