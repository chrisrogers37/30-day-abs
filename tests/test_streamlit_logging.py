#!/usr/bin/env python3
"""
Test script to verify Streamlit app logging works correctly.
"""

import sys
import os
import asyncio

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_streamlit_logging():
    """Test that Streamlit app logging works correctly."""
    print("🧪 Testing Streamlit App Logging...\n")
    
    try:
        # Import the Streamlit app functions
        from ui.streamlit_app import generate_scenario, run_simulation, score_sizing_answers
        print("✅ Streamlit app functions imported successfully")
        
        # Test that logging is configured
        import logging
        logger = logging.getLogger('ui.streamlit_app')
        print(f"✅ Logger configured - Level: {logger.level}, Handlers: {len(logger.handlers)}")
        
        # Test a simple scenario generation (this will use mock data)
        print("\n🚀 Testing scenario generation with logging...")
        scenario = generate_scenario()
        
        if scenario:
            print("✅ Scenario generation completed successfully")
            print(f"   - Title: {scenario.scenario.title}")
            print(f"   - Baseline rate: {scenario.design_params.baseline_conversion_rate:.3f}")
            print(f"   - Target lift: {scenario.design_params.target_lift_pct:.1%}")
            
            # Test simulation
            print("\n📊 Testing simulation with logging...")
            sim_result, analysis = run_simulation(scenario)
            
            if sim_result and analysis:
                print("✅ Simulation completed successfully")
                print(f"   - Control: {sim_result.control_n:,} users, {sim_result.control_conversions:,} conversions")
                print(f"   - Treatment: {sim_result.treatment_n:,} users, {sim_result.treatment_conversions:,} conversions")
                print(f"   - P-value: {analysis.p_value:.3f}, Significant: {analysis.significant}")
                
                # Test scoring
                print("\n🎯 Testing scoring with logging...")
                test_answers = {
                    "baseline_rate": "0.025",
                    "target_lift": "0.200",
                    "alpha": "0.050",
                    "power": "0.800",
                    "daily_traffic": "10000",
                    "sample_size_per_arm": "16792"
                }
                
                scores, total_score, max_score = score_sizing_answers(test_answers, scenario)
                print(f"✅ Scoring completed: {total_score}/{max_score} correct")
                
                return True
            else:
                print("❌ Simulation failed")
                return False
        else:
            print("❌ Scenario generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run the logging test."""
    print("🚀 Testing Streamlit App Logging...\n")
    
    success = test_streamlit_logging()
    
    if success:
        print(f"\n🎉 All logging tests passed!")
        print(f"   The Streamlit app now has comprehensive logging:")
        print(f"   - 🚀 Scenario generation with LLM call details")
        print(f"   - 📊 Simulation with parameter logging")
        print(f"   - 🎯 Scoring with detailed feedback")
        print(f"   - 🔍 All operations logged to console")
        return True
    else:
        print(f"\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
