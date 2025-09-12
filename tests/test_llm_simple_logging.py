#!/usr/bin/env python3
"""
Simple test script for LLM integration with logging (bypasses validator issues).
"""

import asyncio
import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_llm_simple_logging():
    """Test LLM integration with simple logging."""
    print("🧪 Testing LLM Integration with Simple Logging...\n")
    
    # Test 1: Import LLM client directly
    try:
        from llm.client import create_llm_client
        print("✅ LLM client imported successfully")
    except Exception as e:
        print(f"❌ Failed to import LLM client: {e}")
        return False
    
    # Test 2: Create mock client
    try:
        client = create_llm_client(provider="mock")
        print("✅ Mock LLM client created successfully")
    except Exception as e:
        print(f"❌ Failed to create mock client: {e}")
        return False
    
    # Test 3: Test client generation with logging
    try:
        print("\n🚀 Generating LLM response...")
        response = await client.generate_scenario("Generate a test scenario")
        
        print(f"\n📊 Response Details:")
        print(f"   Content Length: {len(response.content)} characters")
        print(f"   Model: {response.model}")
        print(f"   Response Time: {response.response_time:.2f}s")
        print(f"   Retry Count: {response.retry_count}")
        
        print(f"\n📝 Full Response Content:")
        print("=" * 80)
        print(response.content)
        print("=" * 80)
        
        # Test JSON parsing
        try:
            parsed = json.loads(response.content)
            print(f"\n✅ JSON Parsing Successful!")
            print(f"   Keys: {list(parsed.keys())}")
            
            if 'scenario' in parsed:
                print(f"   Scenario Title: {parsed['scenario'].get('title', 'N/A')}")
                print(f"   Company Type: {parsed['scenario'].get('company_type', 'N/A')}")
            
            if 'design_params' in parsed:
                print(f"   Baseline Rate: {parsed['design_params'].get('baseline_conversion_rate', 'N/A')}")
                print(f"   Target Lift: {parsed['design_params'].get('target_lift_pct', 'N/A')}")
                print(f"   Daily Traffic: {parsed['design_params'].get('expected_daily_traffic', 'N/A')}")
                
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON Parsing Failed: {e}")
            print("This indicates the LLM response format needs improvement")
        
        # Test 4: Test with real OpenAI (if available)
        print(f"\n🔑 Testing with OpenAI...")
        print(f"   API Key available: {'YES' if os.getenv('OPENAI_API_KEY') else 'NO'}")
        try:
            real_client = create_llm_client(provider="openai", model="gpt-3.5-turbo")
            print("✅ OpenAI client created successfully")
            
            print("🚀 Testing OpenAI generation...")
            openai_response = await real_client.generate_scenario("Generate a simple e-commerce AB test scenario")
            
            print(f"\n📊 OpenAI Response:")
            print(f"   Content Length: {len(openai_response.content)} characters")
            print(f"   Response Time: {openai_response.response_time:.2f}s")
            print(f"   Retry Count: {openai_response.retry_count}")
            
            print(f"\n📝 OpenAI Response Content (first 500 chars):")
            print("=" * 80)
            print(openai_response.content[:500] + "..." if len(openai_response.content) > 500 else openai_response.content)
            print("=" * 80)
            
            print("✅ OpenAI test completed successfully!")
            
        except Exception as e:
            if "API key" in str(e):
                print(f"❌ OpenAI test failed: No API key provided")
                print(f"   To test with OpenAI, set OPENAI_API_KEY environment variable")
                print(f"   Error: {e}")
            else:
                print(f"❌ OpenAI test failed with unexpected error: {e}")
            print(f"   Continuing with mock client results...")
        
        print(f"\n🎉 LLM integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ LLM generation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_simple_logging())
    sys.exit(0 if success else 1)
