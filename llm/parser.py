"""
JSON Parser Module - Robust LLM Output Parsing and Schema Validation

This module provides comprehensive JSON parsing and schema validation for
LLM-generated scenario data. It handles various JSON formats, provides robust
error recovery, and ensures data integrity through multiple validation layers.

Key Features:
- Multi-strategy JSON extraction from LLM responses
- Comprehensive schema validation with Pydantic
- Business logic validation and consistency checks
- Detailed error reporting with actionable suggestions
- Fallback scenario generation when parsing fails
- Support for various JSON formats (markdown, raw, etc.)
- Robust error recovery and handling

Parsing Strategies:
1. Markdown code block extraction (```json ... ```)
2. Generic code block extraction (``` ... ```)
3. Raw JSON object detection
4. Fallback boundary detection with brace matching

Validation Layers:
1. JSON Structure: Basic JSON syntax and structure validation
2. Schema Validation: Pydantic model validation with type checking
3. Business Logic: Parameter consistency and business rule validation
4. Data Integrity: Cross-field validation and relationship checks

Error Handling:
- Specific exception types for different failure modes
- Detailed error messages with context
- Actionable suggestions for fixing common issues
- Graceful degradation with fallback scenarios
- Comprehensive logging and debugging support

JSON Extraction:
The parser uses multiple strategies to extract JSON from LLM responses:
- Markdown code blocks with language specification
- Generic code blocks without language specification
- Raw JSON objects in the response
- Fallback to brace matching for malformed responses

Schema Validation:
- Comprehensive Pydantic model validation
- Type checking and constraint validation
- Required field validation
- Enum value validation
- Cross-field relationship validation

Business Logic Validation:
- Parameter consistency checks
- Mathematical relationship validation
- Business context appropriateness
- Realism and feasibility assessment

Usage Examples:
    Basic parsing:
        parser = LLMOutputParser()
        result = parser.parse_llm_response(llm_content)
    
    Error handling:
        if not result.success:
            suggestions = parser.get_parsing_suggestions(result.errors)
    
    Fallback scenarios:
        fallback_scenario = parser.create_fallback_scenario()

Dependencies:
- json: Standard JSON parsing
- re: Regular expressions for JSON extraction
- pydantic: Schema validation and data modeling
- schemas.scenario: Scenario DTOs for validation
- logging: Built-in logging support
"""

import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

from pydantic import ValidationError

from schemas.scenario import ScenarioResponseDTO, ScenarioDTO, LlmExpectedDTO
from schemas.design import DesignParamsDTO

from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ParsingResult:
    """
    Comprehensive result dataclass for JSON parsing and validation operations.
    
    This dataclass encapsulates all information about a parsing attempt,
    including the parsed data, validation results, and detailed error/warning
    information for debugging and error recovery.
    
    Attributes:
        success (bool): Whether the parsing and validation was successful
        data (Optional[Dict]): Raw parsed JSON data (if parsing succeeded)
        scenario_dto (Optional[ScenarioResponseDTO]): Validated scenario DTO
        errors (List[str]): List of parsing and validation errors
        warnings (List[str]): List of warnings about the parsed data
        raw_content (str): Original raw content from the LLM response
    
    Examples:
        Check parsing success:
            result = parser.parse_llm_response(llm_content)
            if result.success:
                scenario = result.scenario_dto
                print(f"Parsed scenario: {scenario.scenario.title}")
            else:
                print(f"Parsing failed: {result.errors}")
        
        Analyze warnings:
            for warning in result.warnings:
                print(f"Warning: {warning}")
        
        Access raw data:
            if result.data:
                print(f"Raw JSON keys: {list(result.data.keys())}")
        
        Debug with raw content:
            print(f"Raw LLM response: {result.raw_content[:100]}...")
    """
    success: bool
    data: Optional[Dict] = None
    scenario_dto: Optional[ScenarioResponseDTO] = None
    errors: List[str] = None
    warnings: List[str] = None
    raw_content: str = ""
    
    def __post_init__(self):
        """Initialize empty lists for errors and warnings if None."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class JSONParsingError(Exception):
    """Exception raised when JSON parsing fails."""
    pass


class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass


class LLMOutputParser:
    """
    Parser for LLM-generated JSON outputs with comprehensive validation.
    
    This class provides robust JSON parsing and schema validation for LLM-generated
    scenario data. It handles various JSON formats, provides comprehensive error
    recovery, and ensures data integrity through multiple validation layers.
    
    Features:
        - Multi-strategy JSON extraction from LLM responses
        - Comprehensive schema validation with Pydantic
        - Business logic validation and consistency checks
        - Detailed error reporting with actionable suggestions
        - Fallback scenario generation when parsing fails
        - Support for various JSON formats (markdown, raw, etc.)
        - Robust error recovery and handling
    
    Parsing Strategies:
        1. Markdown code block extraction (```json ... ```)
        2. Generic code block extraction (``` ... ```)
        3. Raw JSON object detection
        4. Fallback boundary detection with brace matching
    
    Validation Layers:
        1. JSON Structure: Basic JSON syntax and structure validation
        2. Schema Validation: Pydantic model validation with type checking
        3. Business Logic: Parameter consistency and business rule validation
        4. Data Integrity: Cross-field validation and relationship checks
    
    Attributes:
        validation_errors (List[str]): List of schema validation errors
        parsing_errors (List[str]): List of JSON parsing errors
    
    Examples:
        Basic parsing:
            parser = LLMOutputParser()
            result = parser.parse_llm_response(llm_content)
        
        Error handling:
            if not result.success:
                suggestions = parser.get_parsing_suggestions(result.errors)
        
        Fallback scenarios:
            fallback_scenario = parser.create_fallback_scenario()
    
    JSON Extraction:
    The parser uses multiple strategies to extract JSON from LLM responses:
    - Markdown code blocks with language specification
    - Generic code blocks without language specification
    - Raw JSON objects in the response
    - Fallback to brace matching for malformed responses
    """
    
    def __init__(self):
        """
        Initialize the parser with empty error tracking lists.
        
        Sets up the parser with empty lists for tracking validation and
        parsing errors during the parsing process.
        """
        self.validation_errors = []
        self.parsing_errors = []
    
    def parse_llm_response(self, content: str) -> ParsingResult:
        """
        Parse and validate LLM response content.
        
        Args:
            content: Raw content from LLM response
            
        Returns:
            ParsingResult with parsed data and validation results
        """
        logger.info(f"Parsing LLM response - Content length: {len(content)} characters")
        logger.debug(f"Raw LLM content: {content[:200]}...")  # First 200 chars
        
        result = ParsingResult(
            success=False,
            raw_content=content
        )
        
        try:
            # Step 1: Clean and extract JSON
            json_content = self._extract_json(content)
            if not json_content:
                logger.error("No valid JSON found in LLM response")
                result.errors.append("No valid JSON found in LLM response")
                return result
            
            logger.info(f"Extracted JSON content - Length: {len(json_content)} characters")
            logger.debug(f"Extracted JSON: {json_content[:300]}...")  # First 300 chars
            
            # Step 2: Parse JSON
            parsed_data = self._parse_json(json_content)
            if not parsed_data:
                logger.error(f"JSON parsing failed: {self.parsing_errors}")
                result.errors.extend(self.parsing_errors)
                return result
            
            logger.info("JSON parsing successful")
            logger.debug(f"Parsed data keys: {list(parsed_data.keys())}")
            result.data = parsed_data
            
            # Step 3: Validate schema
            scenario_dto = self._validate_schema(parsed_data)
            if not scenario_dto:
                logger.error(f"Schema validation failed: {self.validation_errors}")
                result.errors.extend(self.validation_errors)
                return result
            
            logger.info("Schema validation successful")
            result.scenario_dto = scenario_dto
            result.success = True
            
            # Step 4: Additional validation
            self._validate_business_logic(parsed_data, result)
            if result.warnings:
                logger.warning(f"Business logic warnings: {result.warnings}")
            
        except (json.JSONDecodeError, ValidationError, KeyError, ValueError, TypeError) as e:
            logger.error(f"Unexpected error parsing LLM response: {e}")
            result.errors.append(f"Unexpected parsing error: {str(e)}")

        return result
    
    def _extract_json(self, content: str) -> Optional[str]:
        """Extract JSON from LLM response content."""
        # Try to extract JSON from markdown code blocks first
        json_patterns = [
            r'```json\s*(.*?)\s*```',  # ```json ... ```
            r'```\s*(.*?)\s*```',      # ``` ... ```
            r'\{.*\}',                 # Raw JSON object
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                json_content = matches[0].strip()
                # Clean up common JSON issues
                json_content = self._clean_json(json_content)
                if self._is_valid_json_structure(json_content):
                    return json_content
        
        # Fallback: try to find JSON object boundaries
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
            self.parsing_errors.append("No valid JSON found in LLM response")
            return None
        
        json_content = content[start_idx:end_idx + 1]
        
        # Clean up common JSON issues
        json_content = self._clean_json(json_content)
        
        # Basic JSON structure validation
        if not self._is_valid_json_structure(json_content):
            self.parsing_errors.append("Invalid JSON structure")
            return None
        
        return json_content
    
    def _clean_json(self, content: str) -> str:
        """Clean up common JSON formatting issues."""
        # Remove trailing commas before closing braces/brackets
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        # Remove any non-printable characters
        content = ''.join(char for char in content if char.isprintable() or char.isspace())
        
        return content.strip()
    
    def _is_valid_json_structure(self, content: str) -> bool:
        """Check if content has valid JSON structure."""
        try:
            # Quick structure check without full parsing
            if not content.strip().startswith('{') or not content.strip().endswith('}'):
                return False
            
            # Check for balanced braces
            brace_count = 0
            in_string = False
            escape_next = False
            
            for char in content:
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count < 0:
                            return False
            
            return brace_count == 0
            
        except (ValueError, TypeError, IndexError):
            return False

    def _parse_json(self, json_content: str) -> Optional[Dict]:
        """Parse JSON content with error handling."""
        try:
            parsed = json.loads(json_content)
            if not isinstance(parsed, dict):
                self.parsing_errors.append("JSON root must be an object")
                return None
            return parsed
        except json.JSONDecodeError as e:
            self.parsing_errors.append(f"JSON parsing error: {str(e)}")
            return None
        except (ValueError, TypeError) as e:
            self.parsing_errors.append(f"Unexpected JSON error: {str(e)}")
            return None
    
    def _validate_schema(self, data: Dict) -> Optional[ScenarioResponseDTO]:
        """Validate data against Pydantic schemas."""
        self.validation_errors = []
        
        try:
            # Validate required top-level keys
            required_keys = ['scenario', 'design_params', 'llm_expected']
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                self.validation_errors.append(f"Missing required keys: {missing_keys}")
                return None
            
            # Validate scenario
            try:
                scenario_dto = ScenarioDTO(**data['scenario'])
            except ValidationError as e:
                self.validation_errors.append(f"Scenario validation error: {str(e)}")
                return None
            
            # Validate design_params
            try:
                design_dto = DesignParamsDTO(**data['design_params'])
            except ValidationError as e:
                self.validation_errors.append(f"Design params validation error: {str(e)}")
                return None
            
            # Validate llm_expected
            try:
                llm_expected_dto = LlmExpectedDTO(**data['llm_expected'])
            except ValidationError as e:
                self.validation_errors.append(f"LLM expected validation error: {str(e)}")
                return None
            
            # Create response DTO
            response_dto = ScenarioResponseDTO(
                scenario=scenario_dto,
                design_params=design_dto,
                llm_expected=llm_expected_dto,
                generation_metadata={"parser": "llm_parser", "version": "1.0"},
                scenario_id=f"scenario_{hash(str(data)) % 1000000:06d}",
                created_at="2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
            )
            
            return response_dto
            
        except (ValidationError, ValueError, TypeError, KeyError) as e:
            self.validation_errors.append(f"Schema validation error: {str(e)}")
            return None
    
    def _validate_business_logic(self, data: Dict, result: ParsingResult):
        """Validate business logic and consistency."""
        try:
            # Check parameter consistency
            design_params = data.get('design_params', {})
            llm_expected = data.get('llm_expected', {})
            simulation_hints = llm_expected.get('simulation_hints', {})
            
            # Check baseline consistency
            baseline = design_params.get('baseline_conversion_rate')
            control_rate = simulation_hints.get('control_conversion_rate')
            if baseline and control_rate:
                if abs(baseline - control_rate) > 0.001:
                    result.warnings.append(
                        f"Baseline rate ({baseline}) doesn't match control rate ({control_rate})"
                    )
            
            # Check lift consistency
            target_lift = design_params.get('target_lift_pct')
            treatment_rate = simulation_hints.get('treatment_conversion_rate')
            if baseline and treatment_rate and target_lift:
                expected_treatment = baseline * (1 + target_lift)
                actual_lift = (treatment_rate - baseline) / baseline if baseline > 0 else 0
                
                if abs(actual_lift - target_lift) > 0.05:  # 5% tolerance
                    result.warnings.append(
                        f"Target lift ({target_lift:.1%}) doesn't match actual lift ({actual_lift:.1%})"
                    )
            
            # Check allocation consistency
            allocation = design_params.get('allocation', {})
            if allocation:
                control = allocation.get('control', 0)
                treatment = allocation.get('treatment', 0)
                total = control + treatment
                if abs(total - 1.0) > 0.001:
                    result.warnings.append(f"Allocation doesn't sum to 1.0: {total}")
            
            # Check traffic reasonableness
            daily_traffic = design_params.get('expected_daily_traffic', 0)
            if daily_traffic < 500:
                result.warnings.append(f"Daily traffic ({daily_traffic}) may be too low for meaningful testing")
            elif daily_traffic > 1000000:
                result.warnings.append(f"Daily traffic ({daily_traffic}) may be unrealistically high")
            
        except (ValueError, TypeError, KeyError, ZeroDivisionError) as e:
            result.warnings.append(f"Business logic validation error: {str(e)}")
    
    def get_parsing_suggestions(self, errors: List[str]) -> List[str]:
        """Generate suggestions for fixing parsing errors."""
        suggestions = []
        
        for error in errors:
            if "JSON parsing error" in error:
                suggestions.append("Check for unescaped quotes, missing commas, or invalid characters")
            elif "Missing required keys" in error:
                suggestions.append("Ensure all required keys (scenario, design_params, llm_expected) are present")
            elif "validation error" in error:
                suggestions.append("Check parameter ranges and data types according to the schema")
            elif "No valid JSON found" in error:
                suggestions.append("Ensure the response contains valid JSON wrapped in ```json``` blocks")
            else:
                suggestions.append("Review the JSON structure and ensure it matches the required format")
        
        return suggestions
    
    def create_fallback_scenario(self) -> ScenarioResponseDTO:
        """Create a fallback scenario when LLM generation fails."""
        from schemas.shared import CompanyType, UserSegment
        
        fallback_data = {
            "scenario": {
                "title": "Fallback E-commerce Checkout Test",
                "narrative": "A simple checkout button test for e-commerce conversion optimization.",
                "company_type": CompanyType.ECOMMERCE,
                "user_segment": UserSegment.ALL_USERS,
                "primary_kpi": "conversion_rate",
                "secondary_kpis": ["revenue_per_visitor", "cart_abandonment_rate"],
                "unit": "visitor",
                "assumptions": ["traffic is steady", "no seasonality", "users behave independently"]
            },
            "design_params": {
                "baseline_conversion_rate": 0.025,
                "mde_absolute": 0.005,
                "target_lift_pct": 0.20,
                "alpha": 0.10,
                "power": 0.70,
                "allocation": {"control": 0.5, "treatment": 0.5},
                "expected_daily_traffic": 1500
            },
            "llm_expected": {
                "simulation_hints": {
                    "treatment_conversion_rate": 0.030,
                    "control_conversion_rate": 0.025
                },
                "narrative_conclusion": "Expected 20% lift in checkout conversion with sufficient power.",
                "business_interpretation": "Significant revenue impact from improved checkout flow.",
                "risk_assessment": "Low risk - simple UI change with easy rollback.",
                "next_steps": "Monitor for 2 weeks, then analyze and decide on rollout.",
                "notes": "Fallback scenario - LLM generation failed."
            }
        }
        
        return self.parse_llm_response(json.dumps(fallback_data)).scenario_dto
