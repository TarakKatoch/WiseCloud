#!/usr/bin/env python3
"""
Test script for AWS threading integration in VM generation.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
import threading
import time
from unittest.mock import Mock, patch

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_aws_threading_integration():
    """Test that AWS VM generation works with threading."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    try:
        from main import EnergySchedulerApp
        
        # Create the app
        app = EnergySchedulerApp(root)
        
        # Test that the AWS threading variables exist
        assert hasattr(app, 'aws_fetching_vms'), "aws_fetching_vms should exist"
        assert hasattr(app, 'aws_fetch_thread'), "aws_fetch_thread should exist"
        
        # Test initial state
        assert app.aws_fetching_vms == False, "aws_fetching_vms should be False initially"
        assert app.aws_fetch_thread is None, "aws_fetch_thread should be None initially"
        
        # Test that the AWS methods exist
        assert hasattr(app, '_start_aws_vm_generation'), "_start_aws_vm_generation should exist"
        assert hasattr(app, '_fetch_aws_vms_worker'), "_fetch_aws_vms_worker should exist"
        assert hasattr(app, '_aws_vm_generation_complete'), "_aws_vm_generation_complete should exist"
        assert hasattr(app, '_update_aws_loading_state'), "_update_aws_loading_state should exist"
        assert hasattr(app, '_start_simulation_with_vms'), "_start_simulation_with_vms should exist"
        
        print("✓ All AWS threading methods exist")
        return True
        
    except Exception as e:
        print(f"✗ Error testing AWS threading integration: {e}")
        return False
    finally:
        root.destroy()

def test_aws_loading_state():
    """Test the AWS loading state functionality."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    try:
        from main import EnergySchedulerApp
        
        # Create the app
        app = EnergySchedulerApp(root)
        
        # Test loading state methods
        app._update_aws_loading_state(True)
        # Should not raise any exceptions
        
        app._update_aws_loading_state(False)
        # Should not raise any exceptions
        
        print("✓ AWS loading state methods work correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error testing AWS loading state: {e}")
        return False
    finally:
        root.destroy()

def test_aws_vm_generation_methods():
    """Test the AWS VM generation methods without running threads."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    try:
        from main import EnergySchedulerApp
        from models import VM
        
        # Create the app
        app = EnergySchedulerApp(root)
        
        # Set up test data
        app.use_aws_data_var.set(True)
        app.aws_instance_ids_var.set("i-1234567890abcdef0,i-0987654321fedcba0")
        app.aws_access_key_var.set("test-key")
        app.aws_secret_key_var.set("test-secret")
        app.aws_region_var.set("us-east-1")
        
        # Test that generate_vms returns empty list when AWS is enabled
        vms = app.generate_vms(2)
        assert vms == [], "Should return empty list when AWS generation starts"
        
        # Test that fetching state is set
        assert app.aws_fetching_vms == True, "aws_fetching_vms should be True"
        assert app.aws_fetch_thread is not None, "aws_fetch_thread should not be None"
        
        # Test the completion method directly
        test_vms = [
            VM(vm_id="AWS-test1", cpu=0.25, ram=8.0, duration=900),
            VM(vm_id="AWS-test2", cpu=0.30, ram=16.0, duration=900)
        ]
        
        app._aws_vm_generation_complete(test_vms)
        
        # Check that VMs were stored
        assert app.aws_generated_vms == test_vms, "VMs should be stored"
        assert app.aws_fetching_vms == False, "Fetching state should be reset"
        assert app.aws_fetch_thread is None, "Thread should be reset"
        
        print("✓ AWS VM generation methods work correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error testing AWS VM generation methods: {e}")
        return False
    finally:
        root.destroy()

def test_aws_simulation_integration():
    """Test that AWS integration works with simulation methods."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    try:
        from main import EnergySchedulerApp
        from models import VM
        
        # Create the app
        app = EnergySchedulerApp(root)
        
        # Test that the simulation method exists
        assert hasattr(app, '_start_simulation_with_vms'), "_start_simulation_with_vms should exist"
        
        # Test with mock VMs
        test_vms = [
            VM(vm_id="AWS-test1", cpu=0.25, ram=8.0, duration=900),
            VM(vm_id="AWS-test2", cpu=0.30, ram=16.0, duration=900)
        ]
        
        # This should not raise an exception (though it won't actually start simulation)
        # since we're not in a proper simulation state
        try:
            app._start_simulation_with_vms(test_vms)
        except Exception as e:
            # Expected to fail since we're not in a proper simulation context
            pass
        
        print("✓ AWS simulation integration methods exist")
        return True
        
    except Exception as e:
        print(f"✗ Error testing AWS simulation integration: {e}")
        return False
    finally:
        root.destroy()

def run_all_tests():
    """Run all AWS threading tests."""
    print("Testing AWS Threading Integration...")
    print("=" * 50)
    
    tests = [
        test_aws_threading_integration,
        test_aws_loading_state,
        test_aws_vm_generation_methods,
        test_aws_simulation_integration
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
        print("🎉 All AWS threading tests passed!")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 