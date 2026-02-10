# Schemas Module - API Data Transfer Objects (DTOs)

The schemas module provides comprehensive Pydantic-based data transfer objects (DTOs) for the 30 Day A/Bs project. These schemas serve as the API boundaries, ensuring type safety, validation, and clean separation between the core domain logic and external interfaces.

## Overview

This module contains all the data structures used for:
- **API Requests/Responses**: Structured data exchange between client and server
- **LLM Integration**: Data contracts for LLM-generated scenarios
- **Validation**: Comprehensive input validation and bounds checking
- **Serialization**: JSON serialization/deserialization with type safety
- **Documentation**: Self-documenting APIs with field descriptions and constraints

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Layer     │    │   Schemas       │    │   Core Engine   │
│                 │    │                 │    │                 │
│ • REST API      │───▶│ • DTOs          │◀───│ • Domain Types  │
│ • Streamlit UI  │    │ • Validation    │    │ • Business Logic│
│ • External APIs │    │ • Serialization │    │ • Calculations  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   JSON/HTTP     │    │   Pydantic      │    │   Pure Python   │
│                 │    │                 │    │                 │
│ • JSON Schema   │    │ • Field Valid   │    │ • Immutable     │
│ • HTTP Status   │    │ • Type Check    │    │ • Testable      │
│ • Error Handling│    │ • Auto Doc      │    │ • Domain Focus  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Module Structure

### **Core Schema Modules**

#### 1. **`shared.py`** - Common Types and Enums
- **Enums**: TestType, TestDirection, CompanyType, UserSegment, RiskTolerance
- **Common DTOs**: AllocationDTO, DurationConstraintsDTO, BusinessContextDTO
- **Business Logic**: TestQualityDTO, BusinessImpactDTO
- **Validation**: Field validators and constraints

#### 2. **`scenario.py`** - Business Scenarios
- **ScenarioDTO**: Complete business scenario for AB testing
- **SimulationHintsDTO**: LLM-generated hints for simulation parameters
- **LlmExpectedDTO**: LLM's expected outcomes and interpretations
- **Request/Response**: ScenarioRequestDTO, ScenarioResponseDTO

#### 3. **`design.py`** - Test Design Parameters
- **DesignParamsDTO**: Complete design parameters with validation
- **Sample Size**: SampleSizeRequestDTO, SampleSizeResponseDTO
- **Validation**: DesignValidationDTO with feasibility scoring
- **Optimization**: DesignOptimizationDTO with improvement suggestions

#### 4. **`simulate.py`** - Data Simulation
- **User Data**: UserDataDTO for individual user records
- **Simulation**: SimulationRequestDTO, SimulationResponseDTO
- **Configuration**: SimulationConfigDTO with advanced parameters
- **Export**: DataExportDTO for data export configuration

#### 5. **`analyze.py`** - Statistical Analysis
- **Statistics**: TestStatisticsDTO with comprehensive metrics
- **Analysis**: AnalysisRequestDTO, AnalysisResponseDTO
- **Answer Keys**: AnswerKeyDTO for user evaluation
- **Comparison**: AnalysisComparisonDTO, SensitivityAnalysisDTO

#### 6. **`complications.py`** - Experiment Complications
- **ComplicationType**: Types of real-world complications for scenarios
- **ComplicationDTO**: Complication details with impact levels
- **Used by**: LLM generation for adding realism to scenarios

#### 7. **`evaluation.py`** - User Response Scoring
- **Evaluation**: EvaluationCriteriaDTO, EvaluationResponseDTO
- **Scoring**: ScoringRubricDTO with grade thresholds
- **Feedback**: FeedbackTemplateDTO for personalized feedback
- **Metrics**: EvaluationMetricsDTO for system performance

## Key Features

### 🔒 **Type Safety & Validation**
- **Pydantic Models**: Automatic type checking and validation
- **Field Constraints**: Range validation, pattern matching, custom validators
- **Enum Validation**: Strict enum value validation with descriptive options
- **Cross-Field Validation**: Complex validation rules between related fields

### 📋 **Comprehensive Documentation**
- **Field Descriptions**: Every field has detailed documentation
- **Constraint Information**: Clear bounds and validation rules
- **Usage Examples**: Practical examples for common use cases
- **API Documentation**: Auto-generated API docs from schemas

### 🛡️ **Data Integrity**
- **Input Validation**: Comprehensive validation at API boundaries
- **Business Rules**: Domain-specific validation rules
- **Error Handling**: Detailed error messages with context
- **Data Sanitization**: Automatic data cleaning and normalization

### 🔄 **Serialization Support**
- **JSON Schema**: Automatic JSON schema generation
- **Serialization**: Robust JSON serialization/deserialization
- **Backwards Compatibility**: Schema evolution support
- **API Contracts**: Clear contracts between client and server

## Schema Categories

### **Business Context Schemas**

#### Company Types (36 types across 5 industry categories)
```python
class CompanyType(str, Enum):
    # Technology (5)
    SAAS_B2B = "B2B SaaS"
    SAAS_B2C = "B2C SaaS"
    DEVELOPER_TOOLS = "Developer Tools"
    CYBERSECURITY = "Cybersecurity"
    AI_ML_PLATFORM = "AI/ML Platform"

    # Consumer (11)
    ECOMMERCE_DTC = "DTC E-commerce"
    MARKETPLACE = "Marketplace"
    SUBSCRIPTION_BOX = "Subscription Box"
    FOOD_DELIVERY = "Food Delivery"
    TRAVEL = "Travel & Hospitality"
    GAMING = "Gaming"
    STREAMING = "Streaming Media"
    SOCIAL_NETWORK = "Social Network"
    FITNESS_APP = "Fitness/Wellness App"
    DATING_APP = "Dating App"
    NEWS_MEDIA = "News & Media"

    # Financial Services (6)
    NEOBANK = "Neobank"
    INVESTING_APP = "Investing Platform"
    INSURANCE = "Insurtech"
    PAYMENTS = "Payments"
    LENDING = "Lending Platform"
    CRYPTO = "Crypto/Web3"

    # Healthcare (4)
    TELEHEALTH = "Telehealth"
    HEALTH_TRACKING = "Health Tracking"
    PHARMACY = "Digital Pharmacy"
    MENTAL_HEALTH = "Mental Health App"

    # Industrial / B2B (4)
    LOGISTICS = "Logistics"
    HR_TECH = "HR Tech"
    EDTECH = "EdTech"
    REAL_ESTATE = "PropTech"
    # ... plus legacy mappings for backward compatibility
```

#### User Segments (29 segments across 4 dimension categories)
```python
class UserSegment(str, Enum):
    # Lifecycle Stages (8)
    NEW_VISITORS = "first-time visitors"
    NEW_SIGNUPS = "new signups (< 7 days)"
    ACTIVATED_USERS = "activated users"
    ENGAGED_USERS = "weekly active users"
    POWER_USERS = "power users (top 10%)"
    AT_RISK_USERS = "at-risk users (inactive 14+ days)"
    CHURNED_REACTIVATION = "churned users (win-back)"
    DORMANT_USERS = "dormant users (30-90 days inactive)"

    # Value Tiers (6)
    FREE_TIER = "free tier users"
    TRIAL_USERS = "trial users"
    PAID_USERS = "paid subscribers"
    ENTERPRISE = "enterprise accounts"
    HIGH_LTV = "high-LTV customers"
    LOW_LTV = "low-LTV customers"

    # Behavioral Segments (7)
    MOBILE_USERS = "mobile app users"
    DESKTOP_USERS = "desktop users"
    HIGH_INTENT = "high-intent searchers"
    CART_ABANDONERS = "cart abandoners"
    REPEAT_PURCHASERS = "repeat purchasers"
    FIRST_TIME_BUYERS = "first-time buyers"
    BROWSERS = "browsers (no purchase history)"

    # Geographic Segments (4)
    US_USERS = "US users"
    INTERNATIONAL = "international users"
    EMERGING_MARKETS = "emerging market users"
    EU_USERS = "EU users"
    # ... plus legacy mappings for backward compatibility
```

### **Statistical Design Schemas**

#### Design Parameters
```python
class DesignParamsDTO(BaseModel):
    baseline_conversion_rate: float = Field(ge=0.001, le=1.0)
    mde_absolute: float = Field(ge=0.001, le=0.5)
    target_lift_pct: float = Field(ge=-1.0, le=1.0)
    alpha: float = Field(ge=0.01, le=0.1)
    power: float = Field(ge=0.7, le=0.95)
    allocation: AllocationDTO
    expected_daily_traffic: int = Field(ge=1000, le=10000000)
```

#### Sample Size Calculations
```python
class SampleSizeResponseDTO(BaseModel):
    per_arm: int = Field(ge=1)
    total: int = Field(ge=2)
    days_required: int = Field(ge=1)
    power_achieved: float = Field(ge=0.0, le=1.0)
    effect_size: float
    margin_of_error: float = Field(ge=0.0, le=1.0)
```

### **Simulation Schemas**

#### User Data
```python
class UserDataDTO(BaseModel):
    user_id: str
    group: str = Field(pattern="^(control|treatment)$")
    converted: bool
    timestamp: str
    session_id: Optional[str]
    additional_attributes: Dict[str, str] = Field(default_factory=dict)
```

#### Simulation Results
```python
class SimulationResponseDTO(BaseModel):
    control_n: int = Field(ge=1)
    control_conversions: int = Field(ge=0)
    treatment_n: int = Field(ge=1)
    treatment_conversions: int = Field(ge=0)
    user_data: Optional[List[UserDataDTO]]
    simulation_metadata: Dict[str, str]
```

### **Analysis Schemas**

#### Statistical Results
```python
class TestStatisticsDTO(BaseModel):
    test_statistic: float
    p_value: float = Field(ge=0.0, le=1.0)
    confidence_interval: Tuple[float, float]
    confidence_level: float = Field(ge=0.0, le=1.0)
    effect_size: float
    power_achieved: float = Field(ge=0.0, le=1.0)
    degrees_of_freedom: Optional[int]
```

#### Business Impact
```python
class BusinessImpactDTO(BaseModel):
    absolute_lift: float
    relative_lift_pct: float
    revenue_impact_monthly: Optional[float] = Field(None, ge=0)
    confidence_in_revenue: Optional[float] = Field(None, ge=0.0, le=1.0)
    rollout_recommendation: RolloutRecommendation
    risk_level: str = Field(pattern="^(low|medium|high)$")
```

### **Evaluation Schemas**

#### User Response Evaluation
```python
class EvaluationResponseDTO(BaseModel):
    evaluation_criteria: EvaluationCriteriaDTO
    overall_score: float = Field(ge=0.0, le=10.0)
    grade: str
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    interview_feedback: str
    follow_up_questions: List[str]
```

#### Scoring Rubric
```python
class ScoringRubricDTO(BaseModel):
    criteria: Dict[str, Dict[str, float]]
    grade_thresholds: Dict[str, float]
    bonus_points: Dict[str, float] = Field(default_factory=dict)
    penalty_points: Dict[str, float] = Field(default_factory=dict)
```

## Validation System

### **Field-Level Validation**

#### Range Validation
```python
baseline_conversion_rate: float = Field(ge=0.001, le=1.0)  # 0.1% to 100%
alpha: float = Field(ge=0.01, le=0.1)  # 1% to 10%
power: float = Field(ge=0.7, le=0.95)  # 70% to 95%
```

#### Pattern Validation
```python
group: str = Field(pattern="^(control|treatment)$")
complexity_level: str = Field(pattern="^(low|medium|high)$")
format: str = Field(pattern="^(csv|json|parquet)$")
```

#### Custom Validators
```python
@field_validator('allocation')
@classmethod
def validate_allocation_sum(cls, v, info):
    if abs(v.control + v.treatment - 1.0) > 1e-6:
        raise ValueError("Allocation must sum to 1.0")
    return v
```

### **Model-Level Validation**

#### Cross-Field Validation
```python
@field_validator('confidence_interval')
@classmethod
def validate_confidence_interval(cls, v):
    if len(v) != 2:
        raise ValueError("Confidence interval must have exactly 2 values")
    if v[0] >= v[1]:
        raise ValueError("Lower bound must be less than upper bound")
    return v
```

#### Business Logic Validation
```python
@field_validator('true_conversion_rates')
@classmethod
def validate_conversion_rates(cls, v):
    required_keys = {'control', 'treatment'}
    if not required_keys.issubset(v.keys()):
        raise ValueError("Must include 'control' and 'treatment' rates")
    return v
```

## Usage Examples

### **Basic Schema Usage**

#### Creating a Design Request
```python
from schemas.design import DesignParamsDTO, AllocationDTO

allocation = AllocationDTO(control=0.5, treatment=0.5)
design_params = DesignParamsDTO(
    baseline_conversion_rate=0.025,
    mde_absolute=0.005,
    target_lift_pct=0.20,
    alpha=0.05,
    power=0.80,
    allocation=allocation,
    expected_daily_traffic=5000
)
```

#### Scenario Generation
```python
from schemas.scenario import ScenarioRequestDTO
from schemas.shared import CompanyType, UserSegment

request = ScenarioRequestDTO(
    company_type=CompanyType.ECOMMERCE,
    user_segment=UserSegment.ALL_USERS,
    complexity_level="medium",
    include_business_context=True
)
```

#### Analysis Request
```python
from schemas.analyze import AnalysisRequestDTO

analysis_request = AnalysisRequestDTO(
    control_n=1000,
    control_conversions=25,
    treatment_n=1000,
    treatment_conversions=30,
    design_params=design_params,
    test_type="two_proportion_z",
    confidence_level=0.95
)
```

### **Validation Examples**

#### Automatic Validation
```python
try:
    # This will raise ValidationError if constraints are violated
    design = DesignParamsDTO(
        baseline_conversion_rate=0.5,  # Valid: within [0.001, 1.0]
        mde_absolute=0.6,  # Invalid: exceeds 0.5 limit
        # ... other fields
    )
except ValidationError as e:
    print(f"Validation failed: {e}")
```

#### Custom Validation
```python
# Custom validator ensures business logic constraints
@field_validator('target_lift_pct')
@classmethod
def validate_lift_reasonable(cls, v):
    if abs(v) < 0.01:  # Less than 1%
        raise ValueError("Target lift should be at least 1%")
    return v
```

### **Serialization Examples**

#### JSON Serialization
```python
import json

# Convert to JSON
json_data = design_params.model_dump_json()
print(json_data)

# Parse from JSON
parsed = DesignParamsDTO.model_validate_json(json_data)
```

#### API Integration
```python
# FastAPI integration
@app.post("/api/v1/design/compute-sample-size")
async def compute_sample_size(request: SampleSizeRequestDTO) -> SampleSizeResponseDTO:
    # Pydantic automatically validates the request
    result = compute_sample_size_core(request.design_params)
    return SampleSizeResponseDTO(**result)
```

## Integration Points

### **LLM Module Integration**
- **Scenario Generation**: `ScenarioRequestDTO`, `ScenarioResponseDTO`
- **Validation**: Schema validation for LLM outputs
- **Parsing**: JSON parsing with automatic validation

### **Core Engine Integration**
- **Design Parameters**: Conversion between DTOs and core types
- **Simulation**: Data contracts for simulation requests/responses
- **Analysis**: Statistical analysis input/output validation

### **UI Module Integration**
- **Form Validation**: Real-time validation in Streamlit forms
- **Data Display**: Structured data for UI components
- **Error Handling**: User-friendly error messages

## Error Handling

### **Validation Errors**
```python
from pydantic import ValidationError

try:
    invalid_design = DesignParamsDTO(
        baseline_conversion_rate=0.001,
        mde_absolute=0.6,  # Invalid: too large
        # ... other fields
    )
except ValidationError as e:
    # Detailed error information
    for error in e.errors():
        field = error['loc'][0]
        message = error['msg']
        print(f"Field '{field}': {message}")
```

### **Custom Error Messages**
```python
@field_validator('expected_daily_traffic')
@classmethod
def validate_traffic_reasonable(cls, v):
    if v < 1000:
        raise ValueError("Daily traffic must be at least 1,000 for meaningful AB testing")
    return v
```

## Performance Considerations

### **Optimization Features**
- **Lazy Validation**: Validation only when needed
- **Efficient Serialization**: Optimized JSON serialization
- **Memory Efficient**: Minimal memory footprint for DTOs
- **Caching**: Schema compilation caching

### **Best Practices**
- **Immutable DTOs**: Use frozen models where appropriate
- **Minimal DTOs**: Keep DTOs focused and lightweight
- **Validation Boundaries**: Validate at API boundaries only
- **Error Recovery**: Graceful handling of validation failures

## Testing

### **Schema Testing**
```python
import pytest
from pydantic import ValidationError

def test_design_params_validation():
    # Test valid data
    valid_design = DesignParamsDTO(
        baseline_conversion_rate=0.025,
        mde_absolute=0.005,
        # ... other valid fields
    )
    assert valid_design.baseline_conversion_rate == 0.025
    
    # Test invalid data
    with pytest.raises(ValidationError):
        DesignParamsDTO(
            baseline_conversion_rate=1.5,  # Invalid: > 1.0
            # ... other fields
        )
```

### **Integration Testing**
```python
def test_api_integration():
    # Test complete API flow with schemas
    request = SampleSizeRequestDTO(design_params=design_params)
    response = compute_sample_size_api(request)
    assert isinstance(response, SampleSizeResponseDTO)
    assert response.per_arm > 0
```

## Future Enhancements

### **Planned Features**
- **Schema Versioning**: Support for schema evolution
- **Advanced Validation**: More sophisticated business rule validation
- **Performance Monitoring**: Schema validation performance metrics
- **Auto-Documentation**: Enhanced auto-generated documentation

### **Technical Improvements**
- **Custom Types**: Domain-specific custom types
- **Validation Caching**: Cached validation results
- **Schema Registry**: Centralized schema management
- **Migration Tools**: Schema migration utilities

## Contributing

When contributing to the schemas module:

1. **Follow Pydantic Best Practices**: Use appropriate field types and validators
2. **Add Comprehensive Validation**: Include both technical and business validation
3. **Document Thoroughly**: Provide clear field descriptions and examples
4. **Test Validation**: Include tests for both valid and invalid data
5. **Maintain Backwards Compatibility**: Consider existing API contracts

## Dependencies

- **pydantic**: Core validation and serialization framework
- **typing**: Type hints and annotations
- **enum**: Enumeration support
- **json**: JSON serialization support

## License

This module is part of the 30 Day A/Bs project and follows the same MIT license.

