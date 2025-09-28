# LLM Integration Module

The LLM integration module provides comprehensive functionality for generating realistic AB test scenarios using Large Language Models (LLMs). This module orchestrates the complete pipeline from LLM API calls to structured scenario generation, validation, and integration with the core simulation engine.

## Overview

This module serves as the bridge between LLM capabilities and the AB test simulator's core mathematical engine. It handles:

- **LLM Client Management**: Pluggable interface supporting OpenAI, Anthropic, and mock providers
- **Scenario Generation**: Orchestrated generation of realistic business scenarios with retry logic
- **JSON Parsing & Validation**: Robust parsing of LLM outputs with comprehensive error handling
- **Parameter Guardrails**: Validation and clamping of generated parameters to ensure statistical soundness
- **Integration Pipeline**: Complete end-to-end pipeline from scenario generation to simulation analysis

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Client    │    │   Generator     │    │   Integration   │
│                 │    │                 │    │                 │
│ • API Wrapper   │───▶│ • Orchestration │───▶│ • Pipeline      │
│ • Retry Logic   │    │ • Validation    │    │ • Core Bridge   │
│ • Error Handling│    │ • Quality Score │    │ • Analysis      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Guardrails    │    │     Parser      │    │   Prompts       │
│                 │    │                 │    │                 │
│ • Bounds Check  │    │ • JSON Extract  │    │ • Templates     │
│ • Consistency   │    │ • Schema Valid  │    │ • Instructions  │
│ • Clamping      │    │ • Error Recovery│    │ • Constraints   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Module Components

### 1. Client Module (`client.py`)

**Purpose**: Provides a unified interface for LLM API interactions with comprehensive error handling and retry logic.

**Key Features**:
- **Pluggable Providers**: Support for OpenAI, Anthropic, and mock clients
- **Retry Logic**: Exponential backoff with configurable retry attempts
- **Rate Limiting**: Built-in rate limit handling and delays
- **Error Classification**: Specific exception types for different failure modes
- **Response Wrapping**: Standardized response format with metadata

**Key Classes**:
- `LLMClient`: Main client with async support and retry logic
- `LLMConfig`: Configuration dataclass for client settings
- `LLMResponse`: Standardized response format
- `MockLLMClient`: Mock implementation for testing and development

**Usage Example**:
```python
from llm.client import create_llm_client

# Create OpenAI client
client = create_llm_client(
    provider="openai",
    api_key="your-api-key",
    model="gpt-4",
    max_retries=3
)

# Generate completion
response = await client.generate_completion(
    messages=[{"role": "user", "content": "Generate a scenario"}],
    system_prompt="You are a data scientist..."
)
```

### 2. Generator Module (`generator.py`)

**Purpose**: Orchestrates the complete scenario generation process with quality control and retry logic.

**Key Features**:
- **Multi-Attempt Generation**: Configurable retry attempts with quality thresholds
- **Quality Scoring**: Automatic quality assessment of generated scenarios
- **Fallback Scenarios**: Predefined fallback when generation fails
- **Parallel Generation**: Support for generating multiple scenarios simultaneously
- **Request Customization**: Support for custom generation requests

**Key Classes**:
- `LLMScenarioGenerator`: Main generator with comprehensive orchestration
- `GenerationResult`: Result dataclass with detailed metadata
- `ScenarioGenerationError`: Specific exception for generation failures

**Usage Example**:
```python
from llm.generator import create_scenario_generator

# Create generator
generator = create_scenario_generator(provider="mock")

# Generate single scenario
result = await generator.generate_scenario(
    max_attempts=3,
    min_quality_score=0.7
)

if result.success:
    print(f"Generated: {result.scenario_dto.scenario.title}")
    print(f"Quality Score: {result.quality_score:.2f}")
```

### 3. Guardrails Module (`guardrails.py`)

**Purpose**: Provides comprehensive validation and parameter bounds checking for generated scenarios.

**Key Features**:
- **Parameter Bounds**: Strict validation of all statistical parameters
- **Business Context Validation**: Ensures scenarios match company type and user segment
- **Mathematical Consistency**: Validates parameter relationships and calculations
- **Realism Checks**: Flags unrealistic parameter combinations
- **Parameter Clamping**: Automatic correction of out-of-bounds values
- **Quality Scoring**: Quantitative assessment of scenario quality

**Key Classes**:
- `LLMGuardrails`: Main validation engine
- `ValidationResult`: Comprehensive validation results
- `GuardrailError`: Specific exception for validation failures

**Parameter Bounds**:
- `baseline_conversion_rate`: 0.001 to 0.5 (0.1% to 50%)
- `mde_absolute`: 0.001 to 0.1 (0.1% to 10% percentage points)
- `target_lift_pct`: -0.5 to 0.5 (-50% to +50%)
- `alpha`: 0.01 to 0.1 (1% to 10%)
- `power`: 0.7 to 0.95 (70% to 95%)
- `expected_daily_traffic`: 500 to 5,000

**Usage Example**:
```python
from llm.guardrails import LLMGuardrails

guardrails = LLMGuardrails()

# Validate scenario
validation_result = guardrails.validate_scenario(scenario_dto)

if validation_result.is_valid:
    print(f"Quality Score: {validation_result.quality_score:.2f}")
else:
    print(f"Validation Errors: {validation_result.errors}")
```

### 4. Parser Module (`parser.py`)

**Purpose**: Handles robust JSON parsing and schema validation of LLM outputs with comprehensive error recovery.

**Key Features**:
- **JSON Extraction**: Multiple strategies for extracting JSON from LLM responses
- **Schema Validation**: Comprehensive Pydantic schema validation
- **Error Recovery**: Detailed error reporting with suggestions
- **Business Logic Validation**: Additional consistency checks
- **Fallback Generation**: Automatic fallback scenario creation

**Key Classes**:
- `LLMOutputParser`: Main parser with comprehensive validation
- `ParsingResult`: Detailed parsing results with error information
- `JSONParsingError`: Specific exception for JSON parsing failures
- `SchemaValidationError`: Specific exception for schema validation failures

**Parsing Strategies**:
1. Markdown code block extraction (`\`\`\`json ... \`\`\``)
2. Generic code block extraction (`\`\`\` ... \`\`\``)
3. Raw JSON object detection
4. Fallback boundary detection

**Usage Example**:
```python
from llm.parser import LLMOutputParser

parser = LLMOutputParser()

# Parse LLM response
result = parser.parse_llm_response(llm_content)

if result.success:
    scenario_dto = result.scenario_dto
    print(f"Parsed scenario: {scenario_dto.scenario.title}")
else:
    print(f"Parsing Errors: {result.errors}")
    suggestions = parser.get_parsing_suggestions(result.errors)
```

### 5. Integration Module (`integration.py`)

**Purpose**: Provides the complete end-to-end pipeline from LLM scenario generation to simulation analysis.

**Key Features**:
- **Complete Pipeline**: LLM generation → Simulation → Analysis → Comparison
- **Core Type Conversion**: Seamless conversion between DTOs and core domain types
- **Statistical Analysis**: Integration with core statistical analysis engine
- **LLM Comparison**: Comparison of actual results with LLM expectations
- **Comprehensive Reporting**: Detailed pipeline results and summaries

**Key Classes**:
- `LLMIntegration`: Main integration orchestrator
- `SimulationPipelineResult`: Complete pipeline results
- `LLMIntegrationError`: Specific exception for integration failures

**Pipeline Steps**:
1. **Scenario Generation**: Generate scenario using LLM with validation
2. **Type Conversion**: Convert DTOs to core domain types
3. **Sample Size Calculation**: Calculate required sample sizes
4. **Data Simulation**: Generate realistic trial data
5. **Statistical Analysis**: Perform comprehensive statistical tests
6. **LLM Comparison**: Compare actual vs expected results

**Usage Example**:
```python
from llm.integration import create_llm_integration

# Create integration
integration = create_llm_integration(provider="mock")

# Run complete pipeline
result = await integration.run_complete_pipeline(
    max_attempts=3,
    min_quality_score=0.7
)

if result.success:
    summary = integration.get_pipeline_summary(result)
    print(f"Pipeline completed successfully!")
    print(f"Scenario: {summary['scenario']['title']}")
    print(f"P-value: {summary['analysis']['p_value']:.4f}")
```

### 6. Prompts Directory (`prompts/`)

**Purpose**: Contains prompt templates and instructions for LLM scenario generation.

**Key Files**:
- `scenario_prompt.txt`: Comprehensive prompt template for scenario generation

**Prompt Features**:
- **Detailed Instructions**: Comprehensive guidelines for scenario creation
- **Parameter Constraints**: Clear bounds and validation rules
- **Business Context**: Support for multiple company types and user segments
- **Statistical Guidance**: Built-in statistical parameter recommendations
- **Quality Guidelines**: Specific quality criteria and examples

## Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Anthropic Configuration (when implemented)
ANTHROPIC_API_KEY=your-anthropic-api-key

# LLM Configuration
LLM_PROVIDER=openai  # openai, anthropic, mock
LLM_MODEL=gpt-4
LLM_MAX_RETRIES=3
LLM_TIMEOUT=30
```

### Client Configuration

```python
from llm.client import LLMConfig, LLMProvider

config = LLMConfig(
    provider=LLMProvider.OPENAI,
    api_key="your-api-key",
    model="gpt-4",
    max_tokens=4000,
    temperature=0.7,
    timeout=30,
    max_retries=3,
    retry_delay=1.0,
    rate_limit_delay=0.1
)
```

## Error Handling

The module provides comprehensive error handling with specific exception types:

### Exception Hierarchy

```python
LLMError (base)
├── LLMRateLimitError
├── LLMTimeoutError
├── LLMValidationError
├── ScenarioGenerationError
├── JSONParsingError
├── SchemaValidationError
├── GuardrailError
└── LLMIntegrationError
```

### Error Recovery Strategies

1. **Retry Logic**: Exponential backoff with configurable attempts
2. **Parameter Clamping**: Automatic correction of out-of-bounds values
3. **Fallback Scenarios**: Predefined scenarios when generation fails
4. **Quality Thresholds**: Rejection of low-quality scenarios with regeneration
5. **Graceful Degradation**: Partial success handling with detailed error reporting

## Quality Assurance

### Quality Scoring

The module implements a comprehensive quality scoring system:

- **Parameter Realism**: Penalties for unrealistic parameter values
- **Mathematical Consistency**: Validation of parameter relationships
- **Business Context**: Alignment with company type and user segment
- **Statistical Soundness**: Proper parameter bounds and relationships

### Validation Pipeline

1. **JSON Parsing**: Extract and validate JSON structure
2. **Schema Validation**: Pydantic model validation
3. **Business Logic**: Consistency and realism checks
4. **Parameter Bounds**: Statistical parameter validation
5. **Quality Scoring**: Quantitative quality assessment

## Usage Patterns

### Basic Scenario Generation

```python
from llm.generator import create_scenario_generator

# Create generator with mock provider for testing
generator = create_scenario_generator(provider="mock")

# Generate scenario
result = await generator.generate_scenario()

if result.success:
    scenario = result.scenario_dto
    print(f"Generated: {scenario.scenario.title}")
    print(f"Company: {scenario.scenario.company_type}")
    print(f"Quality: {result.quality_score:.2f}")
```

### Complete Pipeline

```python
from llm.integration import create_llm_integration

# Create integration
integration = create_llm_integration(provider="mock")

# Run complete pipeline
result = await integration.run_complete_pipeline()

if result.success:
    # Access all pipeline results
    scenario = result.scenario_dto
    design_params = result.design_params
    sample_size = result.sample_size
    simulation = result.simulation_result
    analysis = result.analysis_result
    comparison = result.comparison
    
    print("Complete pipeline successful!")
```

### Custom Configuration

```python
from llm.client import create_llm_client
from llm.generator import LLMScenarioGenerator

# Create custom client
client = create_llm_client(
    provider="openai",
    api_key="your-key",
    model="gpt-4",
    max_retries=5,
    temperature=0.5
)

# Create generator with custom client
generator = LLMScenarioGenerator(client)

# Generate with custom settings
result = await generator.generate_scenario(
    max_attempts=5,
    min_quality_score=0.8
)
```

## Testing

The module includes comprehensive testing support:

### Mock Client

The mock client provides deterministic responses for testing:

```python
from llm.client import create_llm_client

# Use mock provider for testing
client = create_llm_client(provider="mock")

# Mock responses are deterministic and consistent
response = await client.generate_scenario()
```

### Test Utilities

```python
# Run built-in tests
from llm.generator import test_scenario_generation

# Test scenario generation
result = await test_scenario_generation()
```

## Performance Considerations

### Optimization Features

1. **Async Support**: Full async/await support for concurrent operations
2. **Parallel Generation**: Multiple scenario generation in parallel
3. **Caching**: Response caching for repeated requests (when implemented)
4. **Rate Limiting**: Built-in rate limit handling
5. **Connection Pooling**: Efficient HTTP connection management

### Resource Management

- **Memory Efficient**: Streaming responses for large outputs
- **Timeout Handling**: Configurable timeouts for all operations
- **Error Recovery**: Graceful handling of network issues
- **Resource Cleanup**: Proper cleanup of connections and resources

## Future Enhancements

### Planned Features

1. **Additional Providers**: Anthropic Claude, Google Gemini support
2. **Response Caching**: Redis-based caching for repeated requests
3. **Advanced Prompting**: Dynamic prompt generation based on context
4. **Multi-Modal Support**: Image and document input support
5. **Real-time Streaming**: Streaming responses for long generations
6. **Advanced Analytics**: Detailed usage analytics and monitoring

### Integration Opportunities

1. **API Endpoints**: REST API endpoints for external integration
2. **Webhook Support**: Real-time notifications for generation completion
3. **Batch Processing**: Bulk scenario generation capabilities
4. **Custom Models**: Support for fine-tuned models
5. **A/B Testing**: A/B testing of different prompt strategies

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure valid API keys are configured
2. **Rate Limiting**: Adjust retry delays and rate limit settings
3. **JSON Parsing Errors**: Check LLM response format and prompt clarity
4. **Validation Failures**: Review parameter bounds and business logic
5. **Quality Score Issues**: Adjust quality thresholds or improve prompts

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Run with detailed output
result = await generator.generate_scenario()
```

### Error Analysis

```python
# Analyze generation failures
if not result.success:
    print("Generation failed:")
    for error in result.errors:
        print(f"  - {error}")
    
    print("Suggestions:")
    suggestions = parser.get_parsing_suggestions(result.errors)
    for suggestion in suggestions:
        print(f"  - {suggestion}")
```

## Contributing

When contributing to the LLM module:

1. **Follow Error Handling Patterns**: Use specific exception types
2. **Add Comprehensive Tests**: Include both unit and integration tests
3. **Document New Features**: Update this README and docstrings
4. **Maintain Backward Compatibility**: Ensure existing APIs remain stable
5. **Performance Testing**: Test with various LLM providers and models

## License

This module is part of the 30 Day A/Bs project and follows the same MIT license.
