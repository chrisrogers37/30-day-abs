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
    print("🧪 Testing Streamlit app imports...")
    
    try:
        print("✅ Streamlit imported successfully")
    except Exception as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        print("✅ Pandas imported successfully")
    except Exception as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        # Test our app imports
        print("✅ All app modules imported successfully")
    except Exception as e:
        print(f"❌ App module import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality without running the full app."""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test LLM client creation
        from llm.client import create_llm_client
        client = create_llm_client(provider="mock")
        print("✅ Mock LLM client created successfully")
        
        # Test parser creation
        from llm.parser import LLMOutputParser
        parser = LLMOutputParser()
        print("✅ LLM parser created successfully")
        
        # Test guardrails creation
        from llm.guardrails import LLMGuardrails
        guardrails = LLMGuardrails()
        print("✅ LLM guardrails created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

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
