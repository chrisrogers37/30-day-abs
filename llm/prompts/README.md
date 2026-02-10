# Prompts Directory

This directory contains prompt templates and instructions for LLM scenario generation. The prompts are designed to generate realistic, statistically sound AB test scenarios with proper business context and parameter validation.

## Files

### `scenario_prompt.txt`

The main prompt template for generating AB test scenarios. This comprehensive prompt includes:

**Key Features:**
- Detailed instructions for creating realistic business scenarios
- Statistical parameter constraints and validation rules
- Business context requirements (company types, user segments)
- Mathematical consistency requirements
- Quality guidelines and examples

**Prompt Structure:**
1. **Role Definition**: Expert data scientist and product manager
2. **Requirements**: Detailed scenario generation requirements
3. **JSON Contract**: Strict JSON structure specification
4. **Valid Enum Values**: Allowed values for enums
5. **Parameter Constraints**: Statistical bounds and validation rules
6. **Business Context**: Company types and user segments
7. **Quality Guidelines**: Realism and consistency requirements
8. **Examples**: Good and bad scenario examples

**Parameter Constraints** (enforced by `llm/guardrails.py`):
- `baseline_conversion_rate`: 0.001 to 0.8 (0.1% to 80%)
- `mde_absolute`: 0.001 to 0.2 (0.1% to 20% percentage points)
- `target_lift_pct`: -0.5 to 1.0 (-50% to +100%)
- `alpha`: 0.001 to 0.2 (0.1% to 20%)
- `power`: 0.5 to 0.99 (50% to 99%)
- `expected_daily_traffic`: 100 to 10,000,000 (with traffic tiers from Early Stage to Enterprise)

**Business Context Support:**
- Company Types: 36 types across 5 industry categories (Technology, Consumer, Financial, Healthcare, Industrial/B2B) — see `schemas/shared.py` `CompanyType` enum
- User Segments: 29 segments across 4 dimension categories (Lifecycle, Value Tier, Behavioral, Geographic) — see `schemas/shared.py` `UserSegment` enum
- Primary KPIs: conversion_rate, click_through_rate, revenue_per_user, engagement_rate
- Units: visitor, session, user, impression

**Mathematical Consistency:**
- MDE absolute and target lift percentage must be mathematically consistent
- Baseline and control rates must align
- Allocation proportions must sum to 1.0
- All parameters must be within specified bounds

**Quality Guidelines:**
- Realistic conversion rates and business metrics
- Consistent parameter relationships
- Clear, actionable scenarios
- Complete required fields and realistic secondary KPIs
- Diverse scenarios across different business types

## Usage

The prompt template is automatically loaded by the `LLMScenarioGenerator` class:

```python
from llm.generator import LLMScenarioGenerator

# The generator automatically loads the prompt template
generator = LLMScenarioGenerator(client)
result = await generator.generate_scenario()
```

## Customization

To customize the prompt template:

1. **Edit the template**: Modify `scenario_prompt.txt` to change the generation instructions
2. **Add new constraints**: Include additional parameter bounds or business rules
3. **Update examples**: Add new good/bad scenario examples
4. **Modify JSON structure**: Update the JSON contract to include new fields

## Prompt Engineering Best Practices

### 1. Clear Instructions
- Provide explicit, step-by-step instructions
- Use bullet points and numbered lists for clarity
- Include specific examples and counter-examples

### 2. Constraint Specification
- Define clear parameter bounds and validation rules
- Specify mathematical relationships and consistency requirements
- Include business context validation rules

### 3. JSON Structure
- Provide complete JSON schema with all required fields
- Include type information and constraints
- Show examples of valid JSON structures

### 4. Quality Guidelines
- Define what makes a good scenario
- Provide examples of good and bad scenarios
- Include specific quality criteria

### 5. Error Prevention
- Anticipate common LLM mistakes
- Provide specific guidance for avoiding errors
- Include validation rules and constraints

## Testing and Validation

The prompt template is validated through:

1. **Unit Tests**: Test prompt loading and parsing
2. **Integration Tests**: Test end-to-end scenario generation
3. **Quality Validation**: Test generated scenario quality
4. **Parameter Validation**: Test parameter bounds and consistency

## Future Enhancements

### Planned Improvements
- **Dynamic Prompts**: Context-aware prompt generation
- **Multi-Language Support**: Prompts in different languages
- **Industry-Specific Prompts**: Specialized prompts for different industries
- **A/B Testing**: Test different prompt strategies

### Customization Options
- **Template Variables**: Parameterized prompt templates
- **Conditional Logic**: Dynamic prompt sections based on context
- **External Data**: Integration with external data sources
- **User Preferences**: Customizable prompt parameters

## Troubleshooting

### Common Issues

1. **JSON Parsing Errors**
   - Ensure prompt includes clear JSON structure examples
   - Validate JSON syntax in the prompt
   - Include error handling instructions

2. **Parameter Validation Failures**
   - Verify parameter bounds are clearly specified
   - Include mathematical consistency requirements
   - Provide specific validation examples

3. **Quality Issues**
   - Review quality guidelines and examples
   - Test with different LLM models
   - Iterate on prompt based on results

### Debug Mode

Enable detailed logging to troubleshoot prompt issues:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Run generation with detailed output
result = await generator.generate_scenario()
```

## Contributing

When contributing to the prompts directory:

1. **Test Changes**: Validate prompt changes with multiple LLM models
2. **Document Updates**: Update this README when modifying prompts
3. **Quality Assurance**: Ensure generated scenarios meet quality standards
4. **Backward Compatibility**: Maintain compatibility with existing validation logic

## License

This directory is part of the 30 Day A/Bs project and follows the same MIT license.
