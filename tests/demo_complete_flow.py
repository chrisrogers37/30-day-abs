#!/usr/bin/env python3
"""
Demo script showing the complete LLM flow:
1. Request experiment example and full setup from LLM
2. Extract experiment problem statement and structured outputs from LLM response
3. Validate structured outputs
4. Print the structured outputs in clean manner
"""

import asyncio
import sys
import os
import json
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

def format_json_cleanly(data, indent=2):
    """Format JSON data in a clean, readable manner."""
    return json.dumps(data, indent=indent, ensure_ascii=False)

async def demo_complete_flow():
    """Demonstrate the complete LLM flow."""
    print_section("AB Test Simulator - Complete LLM Flow Demo")
    
    # Step 1: Request experiment example from LLM
    print_subsection("Step 1: Requesting Experiment from LLM")
    
    try:
        from llm.client import create_llm_client
        from llm.parser import LLMOutputParser
        from llm.guardrails import LLMGuardrails
        
        # Create LLM client (use mock for demo, but show OpenAI option)
        use_openai = os.getenv('OPENAI_API_KEY') is not None
        provider = "openai" if use_openai else "mock"
        model = "gpt-3.5-turbo" if use_openai else "gpt-4"
        
        print(f"   Using provider: {provider}")
        if use_openai:
            print(f"   Using model: {model}")
        else:
            print(f"   Using mock client (set OPENAI_API_KEY to use real OpenAI)")
        
        client = create_llm_client(provider=provider, model=model)
        print("   ✅ LLM client created successfully")
        
        # Generate scenario
        print("\n   🚀 Generating experiment scenario...")
        response = await client.generate_scenario("Generate a comprehensive AB test scenario")
        
        print(f"   ✅ LLM response received:")
        print(f"      - Content length: {len(response.content)} characters")
        print(f"      - Response time: {response.response_time:.2f}s")
        print(f"      - Model: {response.model}")
        
    except Exception as e:
        print(f"   ❌ Failed to create LLM client: {e}")
        return False
    
    # Step 2: Extract structured outputs from LLM response
    print_subsection("Step 2: Extracting Structured Outputs")
    
    try:
        parser = LLMOutputParser()
        print("   ✅ Parser created successfully")
        
        # Parse the LLM response
        print("\n   🔍 Parsing LLM response...")
        parse_result = parser.parse_llm_response(response.content)
        
        if parse_result.success:
            print("   ✅ JSON parsing successful!")
            scenario_dto = parse_result.scenario_dto
            print(f"      - Scenario title: {scenario_dto.scenario.title}")
            print(f"      - Company type: {scenario_dto.scenario.company_type}")
            print(f"      - Baseline rate: {scenario_dto.design_params.baseline_conversion_rate:.3f}")
            print(f"      - Target lift: {scenario_dto.design_params.target_lift_pct:.1%}")
        else:
            print(f"   ❌ JSON parsing failed:")
            for error in parse_result.errors:
                print(f"      - {error}")
            return False
            
    except Exception as e:
        print(f"   ❌ Failed to parse LLM response: {e}")
        return False
    
    # Step 3: Validate structured outputs
    print_subsection("Step 3: Validating Structured Outputs")
    
    try:
        guardrails = LLMGuardrails()
        print("   ✅ Guardrails created successfully")
        
        # Validate the parsed data
        print("\n   🔍 Validating structured outputs...")
        validation_result = guardrails.validate_scenario(scenario_dto)
        
        print(f"   📊 Validation Results:")
        print(f"      - Quality Score: {validation_result.quality_score:.2f}/1.0")
        print(f"      - Errors: {len(validation_result.errors)}")
        print(f"      - Warnings: {len(validation_result.warnings)}")
        print(f"      - Suggestions: {len(validation_result.suggestions)}")
        
        if validation_result.errors:
            print(f"   ⚠️ Validation Errors:")
            for error in validation_result.errors:
                print(f"      - {error}")
        
        if validation_result.warnings:
            print(f"   ⚠️ Validation Warnings:")
            for warning in validation_result.warnings:
                print(f"      - {warning}")
        
        if validation_result.suggestions:
            print(f"   💡 Validation Suggestions:")
            for suggestion in validation_result.suggestions:
                print(f"      - {suggestion}")
                
    except Exception as e:
        print(f"   ❌ Failed to validate structured outputs: {e}")
        return False
    
    # Step 4: Print structured outputs in clean manner
    print_section("Step 4: Structured Outputs (Clean Format)")
    
    try:
        # Scenario Information
        print_subsection("📝 Scenario Information")
        scenario = scenario_dto.scenario
        print(f"Title: {scenario.title}")
        print(f"Company Type: {scenario.company_type}")
        print(f"User Segment: {scenario.user_segment}")
        print(f"Primary KPI: {scenario.primary_kpi}")
        print(f"Unit: {scenario.unit}")
        print(f"\nNarrative:")
        print(f"  {scenario.narrative}")
        print(f"\nSecondary KPIs: {', '.join(scenario.secondary_kpis)}")
        print(f"\nAssumptions:")
        for assumption in scenario.assumptions:
            print(f"  • {assumption}")
        
        # Design Parameters
        print_subsection("⚙️ Design Parameters")
        design = scenario_dto.design_params
        print(f"Baseline Conversion Rate: {design.baseline_conversion_rate:.3f} ({design.baseline_conversion_rate:.1%})")
        print(f"Target Lift: {design.target_lift_pct:.1%}")
        print(f"Alpha (Significance Level): {design.alpha}")
        print(f"Power: {design.power}")
        print(f"Expected Daily Traffic: {design.expected_daily_traffic:,}")
        print(f"Allocation:")
        print(f"  • Control: {design.allocation.control:.1%}")
        print(f"  • Treatment: {design.allocation.treatment:.1%}")
        
        # LLM Expected Outcomes
        print_subsection("🎯 LLM Expected Outcomes")
        expected = scenario_dto.llm_expected
        print(f"Simulation Hints:")
        hints = expected.simulation_hints
        print(f"  • control_conversion_rate: {hints.control_conversion_rate:.3f} ({hints.control_conversion_rate:.1%})")
        print(f"  • treatment_conversion_rate: {hints.treatment_conversion_rate:.3f} ({hints.treatment_conversion_rate:.1%})")
        
        print(f"\nNarrative Conclusion:")
        print(f"  {expected.narrative_conclusion}")
        
        print(f"\nBusiness Interpretation:")
        print(f"  {expected.business_interpretation}")
        
        print(f"\nRisk Assessment:")
        print(f"  {expected.risk_assessment}")
        
        print(f"\nNext Steps:")
        print(f"  {expected.next_steps}")
        
        if expected.notes:
            print(f"\nNotes:")
            print(f"  {expected.notes}")
        
        # Raw JSON (for debugging)
        print_subsection("🔧 Raw JSON Output (for debugging)")
        raw_data = {
            "scenario": {
                "title": scenario.title,
                "narrative": scenario.narrative,
                "company_type": scenario.company_type,
                "user_segment": scenario.user_segment,
                "primary_kpi": scenario.primary_kpi,
                "secondary_kpis": scenario.secondary_kpis,
                "unit": scenario.unit,
                "assumptions": scenario.assumptions
            },
            "design_params": {
                "baseline_conversion_rate": design.baseline_conversion_rate,
                "target_lift_pct": design.target_lift_pct,
                "alpha": design.alpha,
                "power": design.power,
                "expected_daily_traffic": design.expected_daily_traffic,
                "allocation": {
                    "control": design.allocation.control,
                    "treatment": design.allocation.treatment
                }
            },
            "llm_expected": {
                "simulation_hints": {
                    "control_conversion_rate": hints.control_conversion_rate,
                    "treatment_conversion_rate": hints.treatment_conversion_rate
                },
                "narrative_conclusion": expected.narrative_conclusion,
                "business_interpretation": expected.business_interpretation,
                "risk_assessment": expected.risk_assessment,
                "next_steps": expected.next_steps,
                "notes": expected.notes
            }
        }
        
        print(format_json_cleanly(raw_data))
        
    except Exception as e:
        print(f"   ❌ Failed to display structured outputs: {e}")
        return False
    
    # Summary
    print_section("✅ Demo Complete - Summary")
    print("The complete LLM flow has been demonstrated:")
    print("1. ✅ Requested experiment from LLM")
    print("2. ✅ Extracted structured outputs from LLM response")
    print("3. ✅ Validated structured outputs with guardrails")
    print("4. ✅ Displayed structured outputs in clean format")
    print("\nAll required elements are present and properly structured!")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(demo_complete_flow())
    sys.exit(0 if success else 1)
