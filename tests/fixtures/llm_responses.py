"""
Mock LLM responses for testing.

This module contains realistic mock LLM responses for testing the LLM integration
layer without making actual API calls.
"""

from typing import Dict, Any


# ============================================================================
# Valid LLM Scenario Responses
# ============================================================================

ECOMMERCE_SCENARIO_RESPONSE = """```json
{
  "scenario": {
    "title": "Product Page Image Carousel Redesign",
    "company_type": "E-commerce",
    "user_segment": "all_users",
    "description": "Testing a new product image carousel with 360-degree view and zoom functionality to improve product engagement and purchase conversion rates.",
    "intervention_description": "Replace static product images with interactive 360-degree carousel that allows users to zoom and rotate product views",
    "primary_metric": "Purchase conversion rate",
    "secondary_metrics": ["Add to cart rate", "Time on product page", "Image interaction rate"],
    "hypothesis": "Interactive product images will increase user confidence and lead to 20% higher purchase conversion rate"
  },
  "design_params": {
    "baseline_conversion_rate": 0.025,
    "mde_absolute": 0.005,
    "target_lift_pct": 0.20,
    "alpha": 0.05,
    "power": 0.80,
    "allocation": {
      "control": 0.5,
      "treatment": 0.5
    },
    "expected_daily_traffic": 5000
  },
  "business_context": {
    "business_target_absolute": 0.004,
    "business_target_relative_pct": 0.16,
    "revenue_per_conversion": 75.0,
    "implementation_cost": 15000.0,
    "risk_tolerance": "medium",
    "minimum_detectable_revenue_impact": 300.0
  },
  "simulation_hints": {
    "expected_control_rate": 0.025,
    "expected_treatment_rate": 0.030,
    "expected_effect_size": 0.15,
    "expected_p_value_range": [0.01, 0.05]
  },
  "llm_expected": {
    "result_interpretation": "If the test achieves the target 20% lift, we expect to see approximately 5 additional purchases per 1000 visitors, generating approximately $375 in additional daily revenue.",
    "statistical_significance_expectation": "With 5000 daily visitors and a 50/50 split, we should reach statistical significance within 3-4 days if the true effect matches our hypothesis.",
    "business_recommendation": "This is a high-impact, medium-risk test. The implementation cost is justified if we achieve even 12-15% lift given the daily traffic volume."
  }
}
```"""


SAAS_SCENARIO_RESPONSE = """```json
{
  "scenario": {
    "title": "Onboarding Flow Simplification",
    "company_type": "SaaS",
    "user_segment": "new_users",
    "description": "Testing a streamlined onboarding process that reduces steps from 5 to 3 to improve activation rates for new user signups.",
    "intervention_description": "Simplified onboarding with progressive disclosure: collect essential info first, defer advanced settings to post-activation",
    "primary_metric": "Activation rate (completing onboarding and first key action)",
    "secondary_metrics": ["Time to activation", "Onboarding completion rate", "Day 7 retention"],
    "hypothesis": "Reducing cognitive load in onboarding will increase activation rate by 25%"
  },
  "design_params": {
    "baseline_conversion_rate": 0.12,
    "mde_absolute": 0.03,
    "target_lift_pct": 0.25,
    "alpha": 0.05,
    "power": 0.80,
    "allocation": {
      "control": 0.5,
      "treatment": 0.5
    },
    "expected_daily_traffic": 2000
  },
  "business_context": {
    "business_target_absolute": 0.024,
    "business_target_relative_pct": 0.20,
    "revenue_per_conversion": 150.0,
    "implementation_cost": 25000.0,
    "risk_tolerance": "low",
    "minimum_detectable_revenue_impact": 720.0
  },
  "simulation_hints": {
    "expected_control_rate": 0.12,
    "expected_treatment_rate": 0.15,
    "expected_effect_size": 0.20,
    "expected_p_value_range": [0.01, 0.04]
  },
  "llm_expected": {
    "result_interpretation": "A successful test would show 3 percentage points improvement in activation, converting approximately 60 additional users daily.",
    "statistical_significance_expectation": "With 2000 daily signups, the test should reach significance in 5-7 days if the hypothesis holds.",
    "business_recommendation": "Critical test for user acquisition efficiency. Even a 15% lift would justify the implementation cost within 2 months."
  }
}
```"""


FINTECH_SCENARIO_RESPONSE = """```json
{
  "scenario": {
    "title": "Account Verification Friction Reduction",
    "company_type": "Fintech",
    "user_segment": "new_users",
    "description": "Testing instant verification via plaid integration versus manual document upload to reduce verification abandonment.",
    "intervention_description": "Replace manual document upload with Plaid instant bank verification for faster, easier account verification",
    "primary_metric": "Verification completion rate",
    "secondary_metrics": ["Time to verification", "Support ticket volume", "Account opening abandonment rate"],
    "hypothesis": "Instant verification will increase completion rate by 35%"
  },
  "design_params": {
    "baseline_conversion_rate": 0.45,
    "mde_absolute": 0.10,
    "target_lift_pct": 0.35,
    "alpha": 0.05,
    "power": 0.85,
    "allocation": {
      "control": 0.5,
      "treatment": 0.5
    },
    "expected_daily_traffic": 1500
  },
  "business_context": {
    "business_target_absolute": 0.09,
    "business_target_relative_pct": 0.30,
    "revenue_per_conversion": 200.0,
    "implementation_cost": 40000.0,
    "risk_tolerance": "medium",
    "minimum_detectable_revenue_impact": 2700.0
  },
  "simulation_hints": {
    "expected_control_rate": 0.45,
    "expected_treatment_rate": 0.55,
    "expected_effect_size": 0.25,
    "expected_p_value_range": [0.001, 0.01]
  },
  "llm_expected": {
    "result_interpretation": "Success means ~150 additional daily verifications, significantly reducing user friction and support costs.",
    "statistical_significance_expectation": "High baseline rate means faster significance - expect results in 3-4 days.",
    "business_recommendation": "High-value test with strong business case. Implementation cost recoverable in under 3 weeks at projected lift."
  }
}
```"""


# ============================================================================
# Invalid/Edge Case Responses
# ============================================================================

MALFORMED_JSON_RESPONSE = """```json
{
  "scenario": {
    "title": "Test Scenario",
    "company_type": "E-commerce"
    # Missing closing bracket and fields
```"""


INVALID_PARAMETERS_RESPONSE = """```json
{
  "scenario": {
    "title": "Invalid Parameter Test",
    "company_type": "Unknown Type",
    "user_segment": "invalid_segment",
    "description": "Testing with invalid parameters"
  },
  "design_params": {
    "baseline_conversion_rate": 1.5,
    "mde_absolute": 2.0,
    "target_lift_pct": 3.0,
    "alpha": 0.50,
    "power": 1.5,
    "allocation": {
      "control": 0.7,
      "treatment": 0.5
    },
    "expected_daily_traffic": 100
  }
}
```"""


MISSING_FIELDS_RESPONSE = """```json
{
  "scenario": {
    "title": "Incomplete Scenario"
  },
  "design_params": {
    "baseline_conversion_rate": 0.05
  }
}
```"""


# ============================================================================
# Response Variations
# ============================================================================

MINIMAL_VALID_RESPONSE = """```json
{
  "scenario": {
    "title": "Minimal Test Scenario",
    "company_type": "SaaS",
    "user_segment": "all_users",
    "description": "A minimal but valid test scenario",
    "intervention_description": "Simple intervention",
    "primary_metric": "Conversion rate",
    "hypothesis": "Will improve conversion by 10%"
  },
  "design_params": {
    "baseline_conversion_rate": 0.05,
    "mde_absolute": 0.005,
    "target_lift_pct": 0.10,
    "alpha": 0.05,
    "power": 0.80,
    "allocation": {
      "control": 0.5,
      "treatment": 0.5
    },
    "expected_daily_traffic": 10000
  }
}
```"""


# ============================================================================
# OpenAI API Response Structures
# ============================================================================

def create_openai_response(content: str, model: str = "gpt-4") -> Dict[str, Any]:
    """
    Create a mock OpenAI API response structure.
    
    Args:
        content: The response content (JSON string)
        model: The model name
    
    Returns:
        Dictionary mimicking OpenAI API response
    """
    return {
        "id": "chatcmpl-mock123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 500,
            "completion_tokens": 800,
            "total_tokens": 1300
        }
    }


# ============================================================================
# Error Responses
# ============================================================================

RATE_LIMIT_ERROR = {
    "error": {
        "message": "Rate limit exceeded",
        "type": "rate_limit_error",
        "code": "rate_limit_exceeded"
    }
}

TIMEOUT_ERROR = {
    "error": {
        "message": "Request timeout",
        "type": "timeout_error",
        "code": "timeout"
    }
}

AUTHENTICATION_ERROR = {
    "error": {
        "message": "Invalid API key",
        "type": "authentication_error",
        "code": "invalid_api_key"
    }
}


# ============================================================================
# Response Collections
# ============================================================================

VALID_RESPONSES = {
    "ecommerce": ECOMMERCE_SCENARIO_RESPONSE,
    "saas": SAAS_SCENARIO_RESPONSE,
    "fintech": FINTECH_SCENARIO_RESPONSE,
    "minimal": MINIMAL_VALID_RESPONSE,
}

INVALID_RESPONSES = {
    "malformed_json": MALFORMED_JSON_RESPONSE,
    "invalid_parameters": INVALID_PARAMETERS_RESPONSE,
    "missing_fields": MISSING_FIELDS_RESPONSE,
}

ERROR_RESPONSES = {
    "rate_limit": RATE_LIMIT_ERROR,
    "timeout": TIMEOUT_ERROR,
    "authentication": AUTHENTICATION_ERROR,
}

