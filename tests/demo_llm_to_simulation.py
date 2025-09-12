#!/usr/bin/env python3
"""
Demo script showing the complete flow from LLM generation to data simulation:
1. Generate scenario from LLM
2. Validate structured outputs
3. Use specifications to simulate experimental data
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_section(title, content=""):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"🔍 {title}")
    print(f"{'='*80}")
    if content:
        print(content)

def print_subsection(title, content=""):
    """Print a formatted subsection header."""
    print(f"\n📋 {title}")
    print(f"{'-'*60}")
    if content:
        print(content)

async def demo_llm_to_simulation():
    """Demonstrate the complete LLM → Validation → Simulation flow."""
    print_section("AB Test Simulator - LLM to Simulation Demo")
    
    # Step 1: Generate scenario from LLM
    print_subsection("Step 1: Generate Scenario from LLM")
    
    try:
        from llm.client import create_llm_client
        from llm.parser import LLMOutputParser
        from llm.guardrails import LLMGuardrails
        
        # Create LLM client
        use_openai = os.getenv('OPENAI_API_KEY') is not None
        provider = "openai" if use_openai else "mock"
        model = "gpt-3.5-turbo" if use_openai else "gpt-4"
        
        print(f"   Using provider: {provider}")
        client = create_llm_client(provider=provider, model=model)
        print("   ✅ LLM client created")
        
        # Generate scenario
        print("   🚀 Generating scenario...")
        response = await client.generate_scenario()
        
        print(f"   ✅ LLM response received ({len(response.content)} chars, {response.response_time:.2f}s)")
        
    except Exception as e:
        print(f"   ❌ LLM generation failed: {e}")
        return False
    
    # Step 2: Parse and validate
    print_subsection("Step 2: Parse and Validate Structured Outputs")
    
    try:
        # Parse LLM response
        parser = LLMOutputParser()
        parse_result = parser.parse_llm_response(response.content)
        
        if not parse_result.success:
            print(f"   ❌ Parsing failed: {parse_result.errors}")
            return False
        
        print("   ✅ JSON parsing successful")
        scenario_dto = parse_result.scenario_dto
        
        # Validate with guardrails
        guardrails = LLMGuardrails()
        validation_result = guardrails.validate_scenario(scenario_dto)
        
        print(f"   📊 Validation Results:")
        print(f"      - Quality Score: {validation_result.quality_score:.2f}/1.0")
        print(f"      - Valid: {validation_result.is_valid}")
        print(f"      - Errors: {len(validation_result.errors)}")
        print(f"      - Warnings: {len(validation_result.warnings)}")
        
        if validation_result.errors:
            print(f"   ⚠️ Validation Errors:")
            for error in validation_result.errors:
                print(f"      - {error}")
        
        if not validation_result.is_valid:
            print("   ❌ Validation failed - cannot proceed to simulation")
            return False
        
        print("   ✅ Validation passed - ready for simulation")
        
    except Exception as e:
        print(f"   ❌ Parsing/validation failed: {e}")
        return False
    
    # Step 3: Extract simulation parameters
    print_subsection("Step 3: Extract Simulation Parameters")
    
    try:
        # Extract key parameters for simulation
        design_params = scenario_dto.design_params
        simulation_hints = scenario_dto.llm_expected.simulation_hints
        
        print(f"   📊 Design Parameters:")
        print(f"      - Baseline Rate: {design_params.baseline_conversion_rate:.3f} ({design_params.baseline_conversion_rate:.1%})")
        print(f"      - Target Lift: {design_params.target_lift_pct:.1%}")
        print(f"      - Daily Traffic: {design_params.expected_daily_traffic:,}")
        print(f"      - Alpha: {design_params.alpha}")
        print(f"      - Power: {design_params.power}")
        
        print(f"   🎯 Simulation Hints:")
        print(f"      - Control Rate: {simulation_hints.control_conversion_rate:.3f} ({simulation_hints.control_conversion_rate:.1%})")
        print(f"      - Treatment Rate: {simulation_hints.treatment_conversion_rate:.3f} ({simulation_hints.treatment_conversion_rate:.1%})")
        
        # Calculate actual lift
        actual_lift = (simulation_hints.treatment_conversion_rate - simulation_hints.control_conversion_rate) / simulation_hints.control_conversion_rate
        print(f"      - Actual Lift: {actual_lift:.1%}")
        
    except Exception as e:
        print(f"   ❌ Parameter extraction failed: {e}")
        return False
    
    # Step 4: Simulate experimental data
    print_subsection("Step 4: Simulate Experimental Data")
    
    try:
        from core.simulate import simulate_trial
        from core.types import DesignParams, Allocation
        
        # Convert DTO to core types
        allocation = Allocation(
            control=design_params.allocation.control,
            treatment=design_params.allocation.treatment
        )
        
        core_design_params = DesignParams(
            baseline_conversion_rate=design_params.baseline_conversion_rate,
            target_lift_pct=design_params.target_lift_pct,
            alpha=design_params.alpha,
            power=design_params.power,
            allocation=allocation,
            expected_daily_traffic=design_params.expected_daily_traffic
        )
        
        # True rates from LLM simulation hints
        true_rates = {
            "control": simulation_hints.control_conversion_rate,
            "treatment": simulation_hints.treatment_conversion_rate
        }
        
        print("   🚀 Running simulation...")
        sim_result = simulate_trial(core_design_params, true_rates, seed=42)
        
        print(f"   ✅ Simulation completed!")
        print(f"   📊 Simulation Results:")
        print(f"      - Control: {sim_result.control_n:,} users, {sim_result.control_conversions:,} conversions")
        print(f"      - Treatment: {sim_result.treatment_n:,} users, {sim_result.treatment_conversions:,} conversions")
        print(f"      - Control Rate: {sim_result.control_rate:.3f} ({sim_result.control_rate:.1%})")
        print(f"      - Treatment Rate: {sim_result.treatment_rate:.3f} ({sim_result.treatment_rate:.1%})")
        print(f"      - Absolute Lift: {sim_result.absolute_lift:.3f} ({sim_result.absolute_lift:.1%})")
        print(f"      - Relative Lift: {sim_result.relative_lift_pct:.1%}")
        
    except Exception as e:
        print(f"   ❌ Simulation failed: {e}")
        return False
    
    # Step 5: Analyze results
    print_subsection("Step 5: Analyze Simulation Results")
    
    try:
        from core.analyze import analyze_results
        
        print("   🔍 Running statistical analysis...")
        analysis = analyze_results(sim_result, alpha=design_params.alpha)
        
        print(f"   ✅ Analysis completed!")
        print(f"   📊 Analysis Results:")
        print(f"      - P-value: {analysis.p_value:.4f}")
        print(f"      - Significant: {analysis.significant}")
        print(f"      - Confidence Interval: ({analysis.confidence_interval[0]:.4f}, {analysis.confidence_interval[1]:.4f})")
        print(f"      - Effect Size: {analysis.effect_size:.3f}")
        print(f"      - Power Achieved: {analysis.power_achieved:.3f}")
        print(f"      - Recommendation: {analysis.recommendation}")
        
    except Exception as e:
        print(f"   ❌ Analysis failed: {e}")
        return False
    
    # Summary
    print_section("✅ Complete Flow Summary")
    print("Successfully demonstrated the complete pipeline:")
    print("1. ✅ Generated scenario from LLM")
    print("2. ✅ Parsed and validated structured outputs")
    print("3. ✅ Extracted simulation parameters")
    print("4. ✅ Simulated experimental data")
    print("5. ✅ Analyzed results with statistical tests")
    print("\n🎯 The system is ready for interview preparation!")
    print("   - LLM generates realistic scenarios")
    print("   - Validation ensures quality")
    print("   - Simulation creates realistic data")
    print("   - Analysis provides statistical insights")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(demo_llm_to_simulation())
    sys.exit(0 if success else 1)
