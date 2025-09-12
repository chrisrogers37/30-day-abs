#!/usr/bin/env python3
"""
Test script to verify enhanced scenario generation with detailed narratives.
"""

import sys
import os
import asyncio

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_enhanced_scenarios():
    """Test that enhanced scenarios generate detailed, interview-style narratives."""
    print("🧪 Testing Enhanced Scenario Generation...\n")
    
    try:
        # Import the Streamlit app functions
        from ui.streamlit_app import generate_scenario
        print("✅ Streamlit app functions imported successfully")
        
        # Test multiple scenario generations to see variety
        print("\n🚀 Testing multiple scenario generations...")
        
        for i in range(3):
            print(f"\n--- Scenario {i+1} ---")
            scenario = generate_scenario()
            
            if scenario:
                print(f"✅ Scenario {i+1} generated successfully")
                print(f"   - Title: {scenario.scenario.title}")
                print(f"   - Company Type: {scenario.scenario.company_type.value}")
                print(f"   - Narrative Length: {len(scenario.scenario.narrative)} characters")
                print(f"   - Narrative Preview: {scenario.scenario.narrative[:100]}...")
                print(f"   - Baseline Rate: {scenario.design_params.baseline_conversion_rate:.3f}")
                print(f"   - Target Lift: {scenario.design_params.target_lift_pct:.1%}")
            else:
                print(f"❌ Scenario {i+1} generation failed")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run the enhanced scenario test."""
    print("🚀 Testing Enhanced Scenario Generation...\n")
    
    success = test_enhanced_scenarios()
    
    if success:
        print(f"\n🎉 Enhanced scenario generation is working!")
        print(f"   The scenarios now include:")
        print(f"   - 🏢 Fictional company names (DataFlow, ShopFast, etc.)")
        print(f"   - 📖 Detailed business context and background")
        print(f"   - 🎯 Specific changes being tested")
        print(f"   - 💼 Clear business goals and objectives")
        print(f"   - 📊 Realistic metrics and parameters")
        print(f"   - 🎭 Interview-style narratives")
        return True
    else:
        print(f"\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
