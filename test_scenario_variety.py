#!/usr/bin/env python3
"""Test script to demonstrate scenario variety."""
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv()

from llm.client import create_llm_client
from llm.generator import LLMScenarioGenerator

async def generate_scenarios():
    client = create_llm_client('openai')
    generator = LLMScenarioGenerator(client)

    scenarios = []
    print("Generating scenarios to demonstrate variety...\n")

    for i in range(3):
        print(f"Generating scenario {i+1}...")
        result = await generator.generate_scenario()
        if result.success:
            s = result.scenario_dto
            scenarios.append({
                'title': s.scenario.title,
                'type': s.scenario.company_type.value,
                'segment': s.scenario.user_segment.value,
                'kpi': s.scenario.primary_kpi,
                'traffic': s.design_params.expected_daily_traffic,
                'baseline': s.design_params.baseline_conversion_rate,
                'lift': s.design_params.target_lift_pct,
                'alpha': s.design_params.alpha,
                'power': s.design_params.power,
                'narrative': s.scenario.narrative[:150] + '...'
            })
        else:
            print(f"  Failed: {result.errors}")
        await asyncio.sleep(2)  # Rate limit

    print("\n" + "="*70)
    print("GENERATED SCENARIOS - DEMONSTRATING VARIETY")
    print("="*70)

    for i, sc in enumerate(scenarios, 1):
        print(f"\n{'='*70}")
        print(f"SCENARIO {i}: {sc['title']}")
        print(f"{'='*70}")
        print(f"  Company Type: {sc['type']}")
        print(f"  User Segment: {sc['segment']}")
        print(f"  Primary KPI:  {sc['kpi']}")
        print(f"  Traffic:      {sc['traffic']:,} daily")
        print(f"  Baseline:     {sc['baseline']:.1%}")
        print(f"  Target Lift:  {sc['lift']:.0%} relative")
        print(f"  Alpha:        {sc['alpha']}")
        print(f"  Power:        {sc['power']}")
        print(f"  Narrative:    {sc['narrative']}")

    # Summary of variety
    print("\n" + "="*70)
    print("VARIETY SUMMARY")
    print("="*70)
    print(f"  Company Types: {set(s['type'] for s in scenarios)}")
    print(f"  User Segments: {set(s['segment'] for s in scenarios)}")
    print(f"  Traffic Range: {min(s['traffic'] for s in scenarios):,} - {max(s['traffic'] for s in scenarios):,}")
    print(f"  Baseline Range: {min(s['baseline'] for s in scenarios):.1%} - {max(s['baseline'] for s in scenarios):.1%}")

if __name__ == '__main__':
    asyncio.run(generate_scenarios())
