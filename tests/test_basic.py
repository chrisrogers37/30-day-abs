#!/usr/bin/env python3
"""
Basic test script to verify core functionality.
"""

import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_core_imports():
    """Test that core modules can be imported."""
    try:
        from core.types import Allocation, DesignParams, SampleSize, SimResult
        print("✅ Core types imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import core types: {e}")
        return False

def test_allocation():
    """Test Allocation class."""
    try:
        from core.types import Allocation
        
        # Test valid allocation
        allocation = Allocation(control=0.5, treatment=0.5)
        assert allocation.control == 0.5
        assert allocation.treatment == 0.5
        assert allocation.total == 1.0
        print("✅ Allocation class works correctly")
        return True
    except Exception as e:
        print(f"❌ Allocation test failed: {e}")
        return False

def test_design_params():
    """Test DesignParams class."""
    try:
        from core.types import DesignParams, Allocation
        
        allocation = Allocation(control=0.5, treatment=0.5)
        params = DesignParams(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.15,
            alpha=0.05,
            power=0.8,
            allocation=allocation,
            expected_daily_traffic=10000
        )
        
        assert params.baseline_conversion_rate == 0.05
        assert params.target_lift_pct == 0.15
        assert params.alpha == 0.05
        assert params.power == 0.8
        assert params.expected_daily_traffic == 10000
        print("✅ DesignParams class works correctly")
        return True
    except Exception as e:
        print(f"❌ DesignParams test failed: {e}")
        return False

def test_sample_size_calculation():
    """Test sample size calculation."""
    try:
        from core.types import DesignParams, Allocation
        from core.design import compute_sample_size
        
        allocation = Allocation(control=0.5, treatment=0.5)
        params = DesignParams(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.15,
            alpha=0.05,
            power=0.8,
            allocation=allocation,
            expected_daily_traffic=10000
        )
        
        sample_size = compute_sample_size(params)
        
        assert sample_size.per_arm > 0
        assert sample_size.total == 2 * sample_size.per_arm
        assert sample_size.days_required > 0
        assert 0 <= sample_size.power_achieved <= 1
        
        print(f"✅ Sample size calculation works: {sample_size.per_arm} per arm, {sample_size.days_required} days")
        return True
    except Exception as e:
        print(f"❌ Sample size calculation test failed: {e}")
        return False

def test_simulation():
    """Test data simulation."""
    try:
        from core.types import DesignParams, Allocation
        from core.simulate import simulate_trial
        
        allocation = Allocation(control=0.5, treatment=0.5)
        params = DesignParams(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.15,
            alpha=0.05,
            power=0.8,
            allocation=allocation,
            expected_daily_traffic=10000
        )
        
        sim_result = simulate_trial(params, seed=42)
        
        assert sim_result.control_n > 0
        assert sim_result.treatment_n > 0
        assert sim_result.control_conversions >= 0
        assert sim_result.treatment_conversions >= 0
        assert sim_result.control_conversions <= sim_result.control_n
        assert sim_result.treatment_conversions <= sim_result.treatment_n
        
        print(f"✅ Simulation works: {sim_result.control_n} control, {sim_result.treatment_n} treatment")
        return True
    except Exception as e:
        print(f"❌ Simulation test failed: {e}")
        return False

def test_analysis():
    """Test statistical analysis."""
    try:
        from core.types import SimResult
        from core.analyze import analyze_results
        
        # Create a simple simulation result
        sim_result = SimResult(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )
        
        analysis = analyze_results(sim_result, alpha=0.05)
        
        assert 0 <= analysis.p_value <= 1
        assert len(analysis.confidence_interval) == 2
        assert analysis.confidence_interval[0] < analysis.confidence_interval[1]
        assert analysis.significant in [True, False]
        assert isinstance(analysis.recommendation, str)
        
        print(f"✅ Analysis works: p-value={analysis.p_value:.4f}, significant={analysis.significant}")
        return True
    except Exception as e:
        print(f"❌ Analysis test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running basic functionality tests...\n")
    
    tests = [
        test_core_imports,
        test_allocation,
        test_design_params,
        test_sample_size_calculation,
        test_simulation,
        test_analysis,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Core functionality is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
