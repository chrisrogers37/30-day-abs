#!/usr/bin/env python3
"""
Test script to verify the Streamlit app can be imported and basic functions work.
"""

import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_streamlit_imports():
    """Test that all required imports work."""
    # Test streamlit import
    import streamlit as st
    assert st is not None, "Streamlit import failed"

    # Test pandas import
    import pandas as pd
    assert pd is not None, "Pandas import failed"

    # Test our app imports
    from llm.client import create_llm_client
    from llm.parser import LLMOutputParser
    from llm.guardrails import LLMGuardrails
    from core.simulate import simulate_trial
    from core.analyze import analyze_results

    assert create_llm_client is not None
    assert LLMOutputParser is not None
    assert LLMGuardrails is not None
    assert simulate_trial is not None
    assert analyze_results is not None

def test_basic_functionality():
    """Test basic functionality without running the full app."""
    # Test LLM client creation
    from llm.client import create_llm_client

    client = create_llm_client(provider="mock")
    assert client is not None, "Mock LLM client creation failed"

    # Test parser creation
    from llm.parser import LLMOutputParser

    parser = LLMOutputParser()
    assert parser is not None, "LLM parser creation failed"

    # Test guardrails creation
    from llm.guardrails import LLMGuardrails

    guardrails = LLMGuardrails()
    assert guardrails is not None, "LLM guardrails creation failed"

def main():
    """Run all tests."""
    print("🚀 Testing Streamlit App Components...\n")
    
    # Test imports
    imports_ok = test_streamlit_imports()
    
    # Test basic functionality
    functionality_ok = test_basic_functionality()
    
    print(f"\n📊 Test Results:")
    print(f"   Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Functionality: {'✅ PASS' if functionality_ok else '❌ FAIL'}")
    
    if imports_ok and functionality_ok:
        print(f"\n🎉 All tests passed! Streamlit app is ready to run.")
        print(f"   To start the app: streamlit run ui/streamlit_app.py")
        return True
    else:
        print(f"\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
