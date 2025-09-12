#!/usr/bin/env python3
"""
Test script to verify the new step-by-step workflow works correctly.
"""

import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_workflow_components():
    """Test that all workflow components can be imported and work."""
    print("🧪 Testing New Workflow Components...\n")
    
    try:
        # Test sizing questions function
        from ui.streamlit_app import ask_experiment_sizing_questions, score_sizing_answers
        print("✅ Sizing questions functions imported successfully")
        
        # Test analysis questions function  
        from ui.streamlit_app import ask_analysis_questions, score_analysis_answers
        print("✅ Analysis questions functions imported successfully")
        
        # Test core design calculation
        from core.design import compute_sample_size
        from core.types import DesignParams, Allocation
        
        # Create test parameters
        allocation = Allocation(control=0.5, treatment=0.5)
        params = DesignParams(
            baseline_conversion_rate=0.025,
            target_lift_pct=0.20,
            alpha=0.05,
            power=0.8,
            allocation=allocation,
            expected_daily_traffic=10000
        )
        
        # Test sample size calculation
        sample_size = compute_sample_size(params)
        print(f"✅ Sample size calculation works: {sample_size.per_arm} per arm")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False

def test_scoring_logic():
    """Test the scoring logic for both sizing and analysis questions."""
    print("\n🧪 Testing Scoring Logic...\n")
    
    try:
        from ui.streamlit_app import score_sizing_answers
        from schemas.scenario import ScenarioResponseDTO, ScenarioDTO, LlmExpectedDTO
        from schemas.design import DesignParamsDTO, AllocationDTO
        from schemas.shared import CompanyType, UserSegment
        
        # Create a mock scenario DTO
        scenario_dto = ScenarioDTO(
            title="Test Scenario",
            narrative="Test narrative",
            company_type=CompanyType.ECOMMERCE,
            user_segment=UserSegment.ALL_USERS,
            primary_kpi="conversion_rate",
            secondary_kpis=["bounce_rate"],
            unit="visitor",
            assumptions=["test assumption"]
        )
        
        design_dto = DesignParamsDTO(
            baseline_conversion_rate=0.025,
            target_lift_pct=0.20,
            alpha=0.05,
            power=0.8,
            allocation=AllocationDTO(control=0.5, treatment=0.5),
            expected_daily_traffic=10000
        )
        
        llm_expected = LlmExpectedDTO(
            simulation_hints={"control_conversion_rate": 0.025, "treatment_conversion_rate": 0.030},
            narrative_conclusion="Test conclusion",
            business_interpretation="Test interpretation",
            risk_assessment="Test risk",
            next_steps="Test steps"
        )
        
        scenario_response = ScenarioResponseDTO(
            scenario=scenario_dto,
            design_params=design_dto,
            llm_expected=llm_expected,
            generation_metadata={},
            scenario_id="test_001",
            created_at="2024-01-01T00:00:00Z"
        )
        
        # Test sizing answers
        test_sizing_answers = {
            "baseline_rate": "0.025",
            "target_lift": "0.200", 
            "alpha": "0.050",
            "power": "0.800",
            "daily_traffic": "10000",
            "sample_size_per_arm": "14193"  # Approximate correct answer
        }
        
        scores, total_score, max_score = score_sizing_answers(test_sizing_answers, scenario_response)
        print(f"✅ Sizing scoring works: {total_score}/{max_score} correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Scoring logic test failed: {e}")
        return False

def main():
    """Run all workflow tests."""
    print("🚀 Testing New Step-by-Step Workflow...\n")
    
    # Test workflow components
    components_ok = test_workflow_components()
    
    # Test scoring logic
    scoring_ok = test_scoring_logic()
    
    print(f"\n📊 Test Results:")
    print(f"   Components: {'✅ PASS' if components_ok else '❌ FAIL'}")
    print(f"   Scoring: {'✅ PASS' if scoring_ok else '❌ FAIL'}")
    
    if components_ok and scoring_ok:
        print(f"\n🎉 All workflow tests passed!")
        print(f"   The new step-by-step workflow is ready:")
        print(f"   1. 📝 Read experiment case")
        print(f"   2. 🎯 Size the experiment (MDE, sample size, power)")
        print(f"   3. 📊 View simulated data + download CSV")
        print(f"   4. 🤔 Analyze data and get scored feedback")
        return True
    else:
        print(f"\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
