#!/usr/bin/env python3
"""
Streamlit app for 30 Day A/Bs - A/B Test Interview Practice.

This app allows users to:
1. Generate realistic A/B test scenarios
2. Download simulated data as CSV
3. Answer analysis questions
4. Get scored feedback on their responses
"""

import streamlit as st
import asyncio
import sys
import os
import pandas as pd
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging for Streamlit
from core.logging import configure_for_streamlit, get_logger, start_quiz_session, configure_quiz_logging

configure_for_streamlit(debug=False)
configure_quiz_logging()  # Configure quiz session logging
logger = get_logger(__name__)

# Import our modules
from llm.client import create_llm_client
from llm.parser import LLMOutputParser
from llm.guardrails import LLMGuardrails
from core.simulate import simulate_trial, export_user_data_csv
from core.analyze import analyze_results
from core.design import compute_sample_size
from core.types import DesignParams, Allocation
from core.validation import validate_design_answer, validate_analysis_answer, score_design_answers, score_analysis_answers
from core.scoring import generate_design_answer_key, generate_analysis_answer_key, create_complete_quiz_result
from schemas.scenario import ScenarioResponseDTO

# Page configuration
st.set_page_config(
    page_title="30 Day A/Bs",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: left;
        margin-bottom: 2rem;
    }
    .scenario-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .metric-box {
        background-color: #e8f4fd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
    }
    .question-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .answer-box {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration constants
MAX_DESIGN_QUESTIONS = 6
MAX_ANALYSIS_QUESTIONS = 7

def initialize_session_state():
    """Initialize session state variables."""
    if 'scenario_data' not in st.session_state:
        st.session_state.scenario_data = None
    if 'simulation_results' not in st.session_state:
        st.session_state.simulation_results = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'sample_size_result' not in st.session_state:
        st.session_state.sample_size_result = None
    if 'design_answers' not in st.session_state:
        st.session_state.design_answers = {}
    if 'design_scoring_results' not in st.session_state:
        st.session_state.design_scoring_results = None
    if 'analysis_answers' not in st.session_state:
        st.session_state.analysis_answers = {}
    if 'completed_questions' not in st.session_state:
        st.session_state.completed_questions = set()
    if 'analysis_scoring_results' not in st.session_state:
        st.session_state.analysis_scoring_results = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "scenario"  # scenario -> design -> data_download -> analysis
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 1  # Track which design question we're on
    if 'current_analysis_question' not in st.session_state:
        st.session_state.current_analysis_question = 1  # Track which analysis question we're on
    if 'completed_analysis_questions' not in st.session_state:
        st.session_state.completed_analysis_questions = set()
    if 'design_answers' not in st.session_state:
        st.session_state.design_answers = {}  # Store answers as we go
    if 'quiz_logger' not in st.session_state:
        st.session_state.quiz_logger = None  # Quiz session logger

def generate_scenario():
    """Generate a new A/B test scenario."""
    logger.info("🚀 Starting scenario generation...")
    
    with st.spinner("🤖 Generating scenario with LLM..."):
        try:
            # Create LLM client
            use_openai = os.getenv('OPENAI_API_KEY') is not None
            provider = "openai" if use_openai else "mock"
            # Read model from environment variable, fallback to gpt-3.5-turbo
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo") if use_openai else "gpt-4"
            
            logger.info(f"🔧 Creating LLM client - Provider: {provider}, Model: {model}")
            client = create_llm_client(provider=provider, model=model)
            
            # Generate scenario
            logger.info("📝 Calling LLM to generate scenario...")
            response = asyncio.run(client.generate_scenario())
            logger.info(f"✅ LLM response received - Length: {len(response.content)} chars, Time: {response.response_time:.2f}s")
            
            # Parse and validate
            logger.info("🔍 Parsing LLM response...")
            parser = LLMOutputParser()
            parse_result = parser.parse_llm_response(response.content)
            
            if not parse_result.success:
                logger.error(f"❌ Parsing failed: {parse_result.errors}")
                st.error(f"❌ Parsing failed: {parse_result.errors}")
                return None
            
            logger.info("✅ Parsing successful, validating with guardrails...")
            
            # Validate with guardrails
            guardrails = LLMGuardrails()
            validation_result = guardrails.validate_scenario(parse_result.scenario_dto)
            
            if not validation_result.is_valid:
                logger.error(f"❌ Validation failed: {validation_result.errors}")
                st.error(f"❌ Validation failed: {validation_result.errors}")
                return None
            
            logger.info(f"✅ Validation successful! Quality score: {validation_result.quality_score:.2f}/1.0")
            if validation_result.warnings:
                logger.warning(f"⚠️ Validation warnings: {validation_result.warnings}")
            if validation_result.suggestions:
                logger.info(f"💡 Validation suggestions: {validation_result.suggestions}")
            
            # Print business context to console
            scenario = parse_result.scenario_dto.scenario
            design = parse_result.scenario_dto.design_params
            llm_expected = parse_result.scenario_dto.llm_expected
            
            logger.info("=" * 80)
            logger.info("📋 BUSINESS CONTEXT FROM LLM:")
            logger.info("=" * 80)
            logger.info(f"🏢 Company Type: {scenario.company_type.value}")
            logger.info(f"👥 User Segment: {scenario.user_segment.value}")
            logger.info(f"📊 Primary KPI: {scenario.primary_kpi}")
            logger.info(f"🎯 Unit of Diversion: {scenario.unit}")
            logger.info(f"📝 Title: {scenario.title}")
            logger.info(f"📖 Narrative: {scenario.narrative}")
            logger.info(f"💭 Assumptions: {', '.join(scenario.assumptions)}")
            if scenario.secondary_kpis:
                logger.info(f"📈 Secondary KPIs: {', '.join(scenario.secondary_kpis)}")
            
            logger.info("-" * 40)
            logger.info("⚙️ DESIGN PARAMETERS:")
            logger.info("-" * 40)
            logger.info(f"📊 Baseline Conversion Rate: {design.baseline_conversion_rate:.3f} ({design.baseline_conversion_rate:.1%})")
            logger.info(f"🎯 Target Lift (MDE): {design.target_lift_pct:.1%} (relative)")
            logger.info(f"📏 Alpha (Significance Level): {design.alpha}")
            logger.info(f"⚡ Power: {design.power}")
            logger.info(f"🚦 Expected Daily Traffic: {design.expected_daily_traffic:,}")
            logger.info(f"⚖️ Allocation: Control {design.allocation.control:.1%}, Treatment {design.allocation.treatment:.1%}")
            
            logger.info("-" * 40)
            logger.info("🎯 LLM EXPECTED OUTCOMES:")
            logger.info("-" * 40)
            logger.info(f"📈 Control Conversion Rate: {llm_expected.simulation_hints.control_conversion_rate:.3f}")
            logger.info(f"📈 Treatment Conversion Rate: {llm_expected.simulation_hints.treatment_conversion_rate:.3f}")
            logger.info(f"💡 Narrative Conclusion: {llm_expected.narrative_conclusion}")
            logger.info(f"💼 Business Interpretation: {llm_expected.business_interpretation}")
            logger.info(f"⚠️ Risk Assessment: {llm_expected.risk_assessment}")
            logger.info(f"🔄 Next Steps: {llm_expected.next_steps}")
            if llm_expected.notes:
                logger.info(f"📝 Notes: {llm_expected.notes}")
            logger.info("=" * 80)
            
            st.success(f"✅ Scenario generated! Quality score: {validation_result.quality_score:.2f}/1.0")
            return parse_result.scenario_dto
            
        except Exception as e:
            logger.error(f"❌ Error generating scenario: {e}")
            st.error(f"❌ Error generating scenario: {e}")
            return None

def run_simulation(scenario_dto):
    """Run simulation based on scenario."""
    logger.info("🚀 Starting simulation...")
    
    with st.spinner("📊 Simulating experimental data..."):
        try:
            # Convert DTO to core types
            design_params = scenario_dto.design_params
            allocation = Allocation(
                control=design_params.allocation.control,
                treatment=design_params.allocation.treatment
            )
            
            core_design_params = DesignParams(
                baseline_conversion_rate=design_params.baseline_conversion_rate,
                target_lift_pct=design_params.target_lift_pct,
                alpha=design_params.alpha,
                power=design_params.power,
                allocation=allocation,
                expected_daily_traffic=design_params.expected_daily_traffic
            )
            
            logger.info(f"📊 Design parameters - Baseline: {design_params.baseline_conversion_rate:.3f}, Target lift: {design_params.target_lift_pct:.1%}, Alpha: {design_params.alpha}, Power: {design_params.power}")
            
            # Calculate sample size
            logger.info("📏 Calculating required sample size...")
            sample_size_result = compute_sample_size(core_design_params)
            
            # Run simulation (core now calculates true rates internally with realistic variation)
            logger.info("🔄 Running simulation with seed=42...")
            sim_result = simulate_trial(core_design_params, seed=42)
            
            logger.info(f"🎯 Actual rates - Control: {sim_result.control_rate:.3f}, Treatment: {sim_result.treatment_rate:.3f}")
            
            # Run analysis
            logger.info("🔍 Running statistical analysis...")
            analysis = analyze_results(sim_result, alpha=design_params.alpha)
            
            logger.info(f"✅ Simulation complete - Control: {sim_result.control_n:,} users ({sim_result.control_conversions:,} conversions), Treatment: {sim_result.treatment_n:,} users ({sim_result.treatment_conversions:,} conversions)")
            logger.info(f"📈 Results - P-value: {analysis.p_value:.6f}, Significant: {analysis.significant}, Power achieved: {analysis.power_achieved:.3f}")
            
            return sim_result, analysis, sample_size_result
            
        except Exception as e:
            logger.error(f"❌ Error running simulation: {e}")
            st.error(f"❌ Error running simulation: {e}")
            return None, None, None

def display_scenario(scenario_dto):
    """Display the scenario information."""
    scenario = scenario_dto.scenario
    design = scenario_dto.design_params
    
    st.markdown("### The Scenario")
    st.markdown(scenario.narrative)

def display_simulation_results(sim_result, analysis):
    """Display simulation results."""
    st.markdown("### 📊 Simulation Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Control Group:**")
        st.metric("Users", f"{sim_result.control_n:,}")
        st.metric("Conversions", f"{sim_result.control_conversions:,}")
        st.metric("Conversion Rate", f"{sim_result.control_rate:.1%}")
    
    with col2:
        st.markdown("**Treatment Group:**")
        st.metric("Users", f"{sim_result.treatment_n:,}")
        st.metric("Conversions", f"{sim_result.treatment_conversions:,}")
        st.metric("Conversion Rate", f"{sim_result.treatment_rate:.1%}")
    
    st.markdown("### 📈 Analysis Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("P-value", f"{analysis.p_value:.6f}")
        st.metric("Significant", "✅ Yes" if analysis.significant else "❌ No")
    
    with col2:
        st.metric("Absolute Lift", f"{sim_result.absolute_lift:.1%}")
        st.metric("Relative Lift", f"{sim_result.relative_lift_pct:.1%}")
    
    with col3:
        st.metric("Effect Size", f"{analysis.effect_size:.3f}")
        st.metric("Power Achieved", f"{analysis.power_achieved:.1%}")

def create_notebook_download():
    """Create Jupyter notebook download button."""
    notebook_path = "notebooks/ab_test_design_template.ipynb"
    
    try:
        with open(notebook_path, 'r') as f:
            notebook_content = f.read()
        
        st.download_button(
            label="📓 Download Design Framework (Jupyter Notebook)",
            data=notebook_content,
            file_name=f"ab_test_design_framework_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ipynb",
            mime="application/json",
            help="Download a Jupyter notebook framework to work through the design questions offline"
        )
        
        st.info("📓 The notebook contains a structured framework for working through all 6 design questions with placeholders for your calculations.")
        
    except FileNotFoundError:
        st.error("❌ Design framework notebook not found. Please ensure the template exists.")

def create_csv_download(sim_result):
    """Create CSV download button."""
    if sim_result.user_data:
        # Convert to DataFrame
        df = pd.DataFrame(sim_result.user_data)
        
        # Create download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV Data",
            data=csv,
            file_name=f"ab_test_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Download the complete user-level data for offline analysis"
        )
        
        st.info(f"📊 CSV contains {len(sim_result.user_data):,} user records with conversion status, session duration, and page views.")

def create_analysis_notebook_download():
    """Create download button for analysis notebook template."""
    import os
    notebook_path = "notebooks/ab_experimental_analysis_template.ipynb"
    
    if os.path.exists(notebook_path):
        with open(notebook_path, "rb") as file:
            notebook_data = file.read()
        
        st.download_button(
            label="📓 Download Analysis Notebook Template",
            data=notebook_data,
            file_name="ab_experimental_analysis_template.ipynb",
            mime="application/json",
            help="Download Jupyter notebook template for analyzing the experimental data"
        )
    else:
        st.error("Analysis notebook template not found.")

def validate_question_answer(question_num, user_answer):
    """Validate a single question answer and return feedback."""
    if not st.session_state.scenario_data:
        return None, None
    
    design = st.session_state.scenario_data.design_params
    allocation = Allocation(control=0.5, treatment=0.5)
    core_design_params = DesignParams(
        baseline_conversion_rate=design.baseline_conversion_rate,
        target_lift_pct=design.target_lift_pct,
        alpha=design.alpha,
        power=design.power,
        allocation=allocation,
        expected_daily_traffic=design.expected_daily_traffic
    )
    sample_size_result = compute_sample_size(core_design_params)
    
    # Use core validation with scenario's mde_absolute
    mde_absolute = design.mde_absolute
    validation_result = validate_design_answer(question_num, user_answer, core_design_params, sample_size_result, mde_absolute)
    return validation_result.is_correct, validation_result.feedback

def validate_analysis_question_answer(question_num, user_answer):
    """Validate a single analysis question answer and return feedback."""
    if not st.session_state.simulation_results:
        return None, None
    
    sim_result = st.session_state.simulation_results
    
    # Get business target for Question 7
    business_target_absolute = None
    if question_num == 7 and st.session_state.scenario_data:
        business_target_absolute = st.session_state.scenario_data.design_params.mde_absolute
    
    # Use core validation
    validation_result = validate_analysis_answer(question_num, user_answer, sim_result, business_target_absolute)
    return validation_result.is_correct, validation_result.feedback

def ask_single_design_question(question_num):
    """Ask a single design question based on question number."""
    st.markdown(f"**Question {question_num} of {MAX_DESIGN_QUESTIONS}**")
    
    if question_num == 1:
        # Question 1: Business's targeted MDE
        st.markdown("**Based on the scenario, what is the business' targeted minimum detectable effect?**")
        mde_absolute = st.number_input(
            "MDE (percentage points):",
            min_value=0.1,
            max_value=50.0,
            value=st.session_state.design_answers.get("mde_absolute", None),
            step=0.1,
            key="mde_absolute_input"
        )
        st.session_state.design_answers["mde_absolute"] = mde_absolute
        
        # Validate and show feedback
        if mde_absolute is not None:
            is_correct, correct_answer = validate_question_answer(1, mde_absolute)
            if is_correct is not None:
                # Log question answer
                if st.session_state.quiz_logger:
                    st.session_state.quiz_logger.log_question_answered(
                        1, mde_absolute, correct_answer, is_correct
                    )
                
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_questions.add(1)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Look for the specific percentage point increase mentioned in the scenario")
    
    elif question_num == 2:
        # Question 2: Target conversion rate calculation
        st.markdown("**Based on the baseline rate and this targeted effect, what would a successful overall conversion rate be?**")
        target_conversion_rate = st.number_input(
            "Target conversion rate (%):",
            min_value=0.1,
            max_value=100.0,
            value=st.session_state.design_answers.get("target_conversion_rate", None),
            step=0.1,
            key="target_conversion_rate_input"
        )
        st.session_state.design_answers["target_conversion_rate"] = target_conversion_rate
        
        # Validate and show feedback
        if target_conversion_rate is not None:
            is_correct, correct_answer = validate_question_answer(2, target_conversion_rate)
            if is_correct is not None:
                # Log question answer
                if st.session_state.quiz_logger:
                    st.session_state.quiz_logger.log_question_answered(
                        2, target_conversion_rate, correct_answer, is_correct
                    )
                
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_questions.add(2)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Calculate: Baseline rate + MDE (absolute)")
    
    elif question_num == 3:
        # Question 3: Relative lift calculation from MDE
        st.markdown("**Based on the scenario's baseline and the business' target minimum detectable effect, calculate the target relative lift**")
        st.markdown("*Hint: Calculate relative lift = (MDE / baseline rate) × 100%*")
        relative_lift_pct = st.number_input(
            "Relative lift (%):",
            min_value=0.1,
            max_value=500.0,
            value=st.session_state.design_answers.get("relative_lift_pct", None),
            step=0.1,
            key="relative_lift_input"
        )
        st.session_state.design_answers["relative_lift_pct"] = relative_lift_pct
        
        # Validate and show feedback
        if relative_lift_pct is not None:
            is_correct, correct_answer = validate_question_answer(3, relative_lift_pct)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_questions.add(3)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Try again: (MDE / Baseline rate) × 100%")
    
    elif question_num == 4:
        # Question 4: Sample size calculation
        if "scenario_data" not in st.session_state or not st.session_state.scenario_data:
            st.error("❌ No scenario available. Please generate a scenario first.")
            return
        scenario = st.session_state.scenario_data
        design = scenario.design_params
        st.markdown(f"**The business has decided to set an alpha of {design.alpha} and a power of {design.power}. Based on the baseline conversion rate, how large of a sample size will we need to detect the targeted effect?**")
        
        # Add helpful resources and formula
        st.markdown("**📚 Resources:**")
        st.markdown("• [Evan Miller's Sample Size Calculator](https://www.evanmiller.org/ab-testing/sample-size.html) - Use this to approximate your answer")
        
        st.markdown("**🧮 Sample Size Formula:**")
        st.markdown("""
        For a **two-proportion z-test**, the sample size per group is:
        
        ```
        n = (z_α/2 + z_β)² × [p₁(1-p₁) + p₂(1-p₂)] / (p₂ - p₁)²
        ```
        
        **Where:**
        - `z_α/2` = Critical value for two-tailed test (1.96 for α = 0.05)
        - `z_β` = Critical value for power (0.841621 for 80% power, one-tailed)
        - `p₁` = Baseline conversion rate
        - `p₂` = Treatment conversion rate = p₁ × (1 + lift%)
        """)
        
        st.markdown("**💡 Tip:** You can use [Evan Miller's calculator](https://www.evanmiller.org/ab-testing/sample-size.html) to approximate your answer, then verify with the formula above. Different calculators may give slightly different results due to formula variations.")
        
        st.markdown("*💡 Hint: Use the two-proportion z-test sample size formula with the given parameters*")
        sample_size = st.number_input(
            "Sample size per group:",
            min_value=100,
            max_value=1000000,
            value=st.session_state.design_answers.get("sample_size_per_group", None),
            step=100,
            key="sample_size_input"
        )
        st.session_state.design_answers["sample_size_per_group"] = sample_size
        
        # Validate and show feedback
        if sample_size is not None:
            is_correct, correct_answer = validate_question_answer(4, sample_size)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_questions.add(4)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Use two-proportion z-test sample size formula")
    
    elif question_num == 5:
        # Question 5: Experiment duration
        if "scenario_data" not in st.session_state or not st.session_state.scenario_data:
            st.error("❌ No scenario available. Please generate a scenario first.")
            return
        scenario = st.session_state.scenario_data
        daily_traffic = scenario.design_params.expected_daily_traffic
        
        st.markdown(f"**The business expects {daily_traffic:,} visitors per day. How long should this experiment run based on the daily traffic and required sample size?**")
        st.markdown("*Hint: Calculate based on daily traffic and the sample size you calculated*")
        duration_days = st.number_input(
            "Duration (days):",
            min_value=1,
            max_value=365,
            value=st.session_state.design_answers.get("experiment_duration_days", None),
            step=1,
            key="duration_input"
        )
        
        # Update session state immediately
        st.session_state.design_answers["experiment_duration_days"] = duration_days
        
        # Validate and show feedback only if user has entered a value
        if duration_days is not None:
            is_correct, correct_answer = validate_question_answer(5, duration_days)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_questions.add(5)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Calculate: Required sample size ÷ Daily traffic")
    
    elif question_num == 6:
        # Question 6: Business Impact Calculation
        st.markdown("**How many additional conversions per day would this experiment detect if successful?**")
        st.markdown("*Hint: Calculate based on daily traffic and the absolute lift*")
        additional_conversions = st.number_input(
            "Additional conversions per day:",
            min_value=1,
            max_value=10000,
            value=st.session_state.design_answers.get("additional_conversions_per_day", None),
            step=1,
            key="additional_conversions_input"
        )
        st.session_state.design_answers["additional_conversions_per_day"] = additional_conversions
        
        # Validate and show feedback
        if additional_conversions is not None:
            is_correct, correct_answer = validate_question_answer(6, additional_conversions)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_questions.add(6)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Calculate: Daily traffic × MDE (absolute)")
    

def ask_single_analysis_question(question_num):
    """Ask a single analysis question based on question number."""
    st.markdown(f"**Question {question_num} of {MAX_ANALYSIS_QUESTIONS}**")
    
    if question_num == 1:
        # Question 1: Control conversion rate
        st.markdown("**What is the conversion rate for the control group?**")
        st.markdown("*Hint: Calculate conversions ÷ total users in the control group*")
        
        control_rate = st.number_input(
            "Control conversion rate (%):",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.analysis_answers.get("control_conversion_rate", None),
            step=0.001,
            format="%.3f",
            key="control_rate_input",
            help="Enter as percentage (e.g., 2.5 for 2.5%)"
        )
        st.session_state.analysis_answers["control_conversion_rate"] = control_rate
        
        # Validate and show feedback
        if control_rate is not None:
            is_correct, correct_answer = validate_analysis_question_answer(1, control_rate)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_analysis_questions.add(1)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Look at the control group data in the CSV file")
    
    elif question_num == 2:
        # Question 2: Treatment conversion rate
        st.markdown("**What is the conversion rate for the treatment group?**")
        st.markdown("*Hint: Calculate conversions ÷ total users in the treatment group*")
        
        treatment_rate = st.number_input(
            "Treatment conversion rate (%):",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.analysis_answers.get("treatment_conversion_rate", None),
            step=0.001,
            format="%.3f",
            key="treatment_rate_input",
            help="Enter as percentage (e.g., 2.7 for 2.7%)"
        )
        st.session_state.analysis_answers["treatment_conversion_rate"] = treatment_rate
        
        # Validate and show feedback
        if treatment_rate is not None:
            is_correct, correct_answer = validate_analysis_question_answer(2, treatment_rate)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_analysis_questions.add(2)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Look at the treatment group data in the CSV file")
    
    elif question_num == 3:
        # Question 3: Absolute lift
        st.markdown("**What is the absolute lift between treatment and control groups?**")
        st.markdown("*Hint: Calculate treatment rate - control rate (in percentage points)*")
        
        absolute_lift = st.number_input(
            "Absolute lift (percentage points):",
            min_value=-100.0,
            max_value=100.0,
            value=st.session_state.analysis_answers.get("absolute_lift", None),
            step=0.001,
            format="%.3f",
            key="absolute_lift_input",
            help="Enter as percentage points (e.g., 0.2 for 0.2 percentage points)"
        )
        st.session_state.analysis_answers["absolute_lift"] = absolute_lift
        
        # Validate and show feedback
        if absolute_lift is not None:
            is_correct, correct_answer = validate_analysis_question_answer(3, absolute_lift)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_analysis_questions.add(3)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Calculate: Treatment Rate - Control Rate")
    
    elif question_num == 4:
        # Question 4: Relative lift
        st.markdown("**What is the relative lift between treatment and control groups?**")
        st.markdown("*Hint: Calculate (treatment rate - control rate) ÷ control rate × 100*")
        
        relative_lift = st.number_input(
            "Relative lift (%):",
            min_value=-1000.0,
            max_value=1000.0,
            value=st.session_state.analysis_answers.get("relative_lift", None),
            step=0.1,
            format="%.1f",
            key="relative_lift_input",
            help="Enter as percentage (e.g., 8.0 for 8.0%)"
        )
        st.session_state.analysis_answers["relative_lift"] = relative_lift
        
        # Validate and show feedback
        if relative_lift is not None:
            is_correct, correct_answer = validate_analysis_question_answer(4, relative_lift)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_analysis_questions.add(4)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Calculate: (Treatment Rate - Control Rate) ÷ Control Rate × 100")
    
    elif question_num == 5:
        # Question 5: Statistical significance (P-value)
        st.markdown("**What is the p-value for the difference between treatment and control groups?**")
        st.markdown("*Hint: Perform a two-proportion z-test to determine statistical significance*")
        
        p_value = st.number_input(
            "P-value:",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.analysis_answers.get("p_value", None),
            step=0.001,
            format="%.3f",
            key="p_value_input",
            help="Enter as decimal (e.g., 0.023 for 2.3%)"
        )
        st.session_state.analysis_answers["p_value"] = p_value
        
        # Validate and show feedback
        if p_value is not None:
            is_correct, correct_answer = validate_analysis_question_answer(5, p_value)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_analysis_questions.add(5)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Use statsmodels.stats.proportion.proportions_ztest or scipy.stats")
    
    elif question_num == 6:
        # Question 6: Confidence interval for difference
        st.markdown("**What is the 95% confidence interval for the difference between treatment and control groups?**")
        st.markdown("*Hint: Calculate the confidence interval for (treatment rate - control rate)*")
        
        col1, col2 = st.columns(2)
        with col1:
            ci_lower = st.number_input(
                "Lower bound (%):",
                min_value=-100.0,
                max_value=100.0,
                value=st.session_state.analysis_answers.get("ci_lower", None),
                step=0.01,
                format="%.2f",
                key="ci_lower_input",
                help="Enter as percentage (e.g., 0.8 for 0.8%)"
            )
            st.session_state.analysis_answers["ci_lower"] = ci_lower
        
        with col2:
            ci_upper = st.number_input(
                "Upper bound (%):",
                min_value=-100.0,
                max_value=100.0,
                value=st.session_state.analysis_answers.get("ci_upper", None),
                step=0.01,
                format="%.2f",
                key="ci_upper_input",
                help="Enter as percentage (e.g., 3.2 for 3.2%)"
            )
            st.session_state.analysis_answers["ci_upper"] = ci_upper
        
        # Validate and show feedback
        if ci_lower is not None and ci_upper is not None:
            is_correct, correct_answer = validate_analysis_question_answer(6, (ci_lower, ci_upper))
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_analysis_questions.add(6)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Calculate: (p1 - p2) ± z_α/2 × SE(p1 - p2)")
    
    elif question_num == 7:
        # Question 7: Rollout decision
        st.markdown("**Based on the confidence interval and business target, what is your rollout recommendation?**")
        st.markdown("*Hint: Compare the confidence interval bounds to the business target lift*")
        
        # Get business target from scenario
        business_target_pct = st.session_state.scenario_data.design_params.target_lift_pct * 100
        business_target_absolute = st.session_state.scenario_data.design_params.mde_absolute * 100
        
        st.info(f"**Business Target:** {business_target_pct:.1f}% relative lift ({business_target_absolute:.2f}% absolute lift)")
        
        rollout_decision = st.selectbox(
            "Rollout Decision:",
            ["proceed_with_confidence", "proceed_with_caution", "do_not_proceed"],
            format_func=lambda x: {
                "proceed_with_confidence": "Proceed with Confidence",
                "proceed_with_caution": "Proceed with Caution", 
                "do_not_proceed": "Do Not Proceed"
            }[x],
            index=None,  # No default selection
            key="rollout_decision_input"
        )
        st.session_state.analysis_answers["rollout_decision"] = rollout_decision
        
        # Validate and show feedback
        if rollout_decision:
            is_correct, correct_answer = validate_analysis_question_answer(7, rollout_decision)
            if is_correct is not None:
                if is_correct:
                    st.success("✅ Correct!")
                    st.session_state.completed_analysis_questions.add(7)
                else:
                    st.error("❌ Incorrect. Try again.")
                    st.info("💡 Consider: Is the business target achievable within the confidence interval?")

def ask_data_analysis_questions():
    """Ask data analysis questions after downloading the CSV."""
    st.markdown("### 🔍 Data Analysis Questions")
    st.markdown("After downloading and examining the CSV data, answer these questions:")
    
    answers = {}
    
    # Question 1: Control conversion rate
    st.markdown(f"**Question 1: What is the conversion rate for the control group?**")
    st.markdown("*Hint: Calculate conversions ÷ total users in the control group*")
    
    control_rate = st.number_input(
        "Control conversion rate (%):",
        min_value=0.0,
        max_value=100.0,
        value=None,
        step=0.001,
        format="%.3f",
        key="control_rate_input",
        help="Enter as percentage (e.g., 2.5 for 2.5%)"
    )
    answers["control_conversion_rate"] = control_rate
    
    # Question 2: Treatment conversion rate
    st.markdown(f"**Question 2: What is the conversion rate for the treatment group?**")
    st.markdown("*Hint: Calculate conversions ÷ total users in the treatment group*")
    
    treatment_rate = st.number_input(
        "Treatment conversion rate (%):",
        min_value=0.0,
        max_value=100.0,
        value=None,
        step=0.001,
        format="%.3f",
        key="treatment_rate_input",
        help="Enter as percentage (e.g., 2.7 for 2.7%)"
    )
    answers["treatment_conversion_rate"] = treatment_rate
    
    return answers

def score_data_analysis_answers(user_answers, sim_result):
    """Score data analysis questions against simulation results."""
    logger.info("🔍 Starting data analysis answers scoring...")
    
    # Transform answers to match expected format
    transformed_answers = user_answers.copy()
    
    # Convert confidence interval from separate ci_lower/ci_upper to tuple
    if "ci_lower" in user_answers and "ci_upper" in user_answers:
        ci_lower = user_answers.get("ci_lower")
        ci_upper = user_answers.get("ci_upper")
        if ci_lower is not None and ci_upper is not None:
            transformed_answers["confidence_interval"] = (ci_lower, ci_upper)
    
    # Get business target for Question 7
    business_target_absolute = None
    if st.session_state.scenario_data:
        business_target_absolute = st.session_state.scenario_data.design_params.mde_absolute
    
    # Use core scoring
    scoring_result = score_analysis_answers(transformed_answers, sim_result, business_target_absolute)
    return scoring_result.scores, scoring_result.total_score, scoring_result.max_score


def display_scoring_results(scores, total_score, max_score):
    """Display scoring results."""
    st.markdown("### 📊 Your Results")
    
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score", f"{total_score}/{max_score}")
    with col2:
        st.metric("Percentage", f"{percentage:.1f}%")
    with col3:
        st.metric("Grade", "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D" if percentage >= 60 else "F")
    
    # Log quiz completion for design questions
    if st.session_state.quiz_logger:
        correct_count = sum(1 for result in scores.values() if result["correct"])
        feedback_lines = []
        for key, result in scores.items():
            status = "✅ Correct" if result["correct"] else "❌ Incorrect"
            feedback_lines.append(f"{key.replace('_', ' ').title()}: {result['user']} ({status})")
        
        feedback = "\n".join(feedback_lines)
        st.session_state.quiz_logger.log_quiz_completed(
            percentage/100, feedback, max_score, correct_count
        )
    
    st.markdown("### 📝 Detailed Feedback")
    
    for key, result in scores.items():
        if result["correct"]:
            st.success(f"✅ **{key.replace('_', ' ').title()}**: {result['user']} (Correct!)")
        else:
            st.error(f"❌ **{key.replace('_', ' ').title()}**: {result['user']} (Correct answer: {result['correct']})")

def display_analysis_scoring_results(scores, total_score, max_score):
    """Display analysis scoring results with proper question names."""
    st.markdown("### 📊 Analysis Results")
    
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score", f"{total_score}/{max_score}")
    with col2:
        st.metric("Percentage", f"{percentage:.1f}%")
    with col3:
        st.metric("Grade", "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D" if percentage >= 60 else "F")
    
    st.markdown("### 📝 Detailed Feedback")
    
    # Question name mapping
    question_names = {
        "control_conversion_rate": "Question 1: Control Conversion Rate",
        "treatment_conversion_rate": "Question 2: Treatment Conversion Rate", 
        "absolute_lift": "Question 3: Absolute Lift",
        "relative_lift": "Question 4: Relative Lift",
        "p_value": "Question 5: Statistical Significance (P-value)",
        "confidence_interval": "Question 6: Confidence Interval",
        "rollout_decision": "Question 7: Rollout Decision"
    }
    
    for key, result in scores.items():
        question_name = question_names.get(key, key.replace('_', ' ').title())
        if result["correct"]:
            st.success(f"✅ **{question_name}**: {result['user']} (Correct!)")
        else:
            st.error(f"❌ **{question_name}**: {result['user']} (Correct answer: {result['correct_answer']})")

def score_design_answers(user_answers, scenario_data, sample_size_result):
    """Score the design questions against correct values"""
    logger.info("🎯 Starting design answers scoring...")
    st.markdown("### 📊 Design Results")
    
    # Convert scenario data to core types
    design = scenario_data.design_params
    allocation = Allocation(control=0.5, treatment=0.5)
    core_design_params = DesignParams(
        baseline_conversion_rate=design.baseline_conversion_rate,
        target_lift_pct=design.target_lift_pct,
        alpha=design.alpha,
        power=design.power,
        allocation=allocation,
        expected_daily_traffic=design.expected_daily_traffic
    )
    
    # Use core scoring with scenario's mde_absolute
    from core.validation import score_design_answers as core_score_design_answers
    mde_absolute = design.mde_absolute
    scoring_result = core_score_design_answers(user_answers, core_design_params, sample_size_result, mde_absolute)
    
    # Display results
    percentage = scoring_result.percentage
    st.markdown(f"**Score: {scoring_result.total_score}/{scoring_result.max_score} ({percentage:.1f}%)**")
    
    logger.info(f"📊 Design scoring complete: {scoring_result.total_score}/{scoring_result.max_score} correct")
    return scoring_result.scores, scoring_result.total_score, scoring_result.max_score

def main():
    """Main Streamlit app."""
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Practice Session")
        
        if st.button("🔄 Generate New Scenario", type="primary"):
            # Start new quiz session
            st.session_state.quiz_logger = start_quiz_session()
            st.session_state.quiz_logger.log_user_action("New Quiz Session Started")
            
            st.session_state.scenario_data = generate_scenario()
            if st.session_state.scenario_data:
                # Log scenario generation
                scenario_dict = {
                    'scenario': {
                        'title': st.session_state.scenario_data.scenario.title,
                        'company': st.session_state.scenario_data.scenario.company,
                        'industry': st.session_state.scenario_data.scenario.industry,
                        'baseline_conversion_rate': st.session_state.scenario_data.design_params.baseline_conversion_rate,
                        'target_lift_pct': st.session_state.scenario_data.design_params.target_lift_pct,
                        'expected_daily_traffic': st.session_state.scenario_data.design_params.expected_daily_traffic,
                        'business_context': st.session_state.scenario_data.scenario.business_context
                    }
                }
                st.session_state.quiz_logger.log_scenario_generated(scenario_dict)
                
                st.session_state.design_answers = {}
                st.session_state.design_scoring_results = None
                st.session_state.current_question = 1  # Reset to first question
                st.session_state.completed_questions = set()  # Reset completed questions
                st.session_state.analysis_answers = {}
                st.session_state.analysis_scoring_results = None
                st.session_state.current_step = "scenario"
                
                # Run simulation and analysis immediately after scenario generation
                sim_result, analysis_result, sample_size_result = run_simulation(st.session_state.scenario_data)
                st.session_state.simulation_results = sim_result
                st.session_state.analysis_results = analysis_result
                st.session_state.sample_size_result = sample_size_result
                
                # Log simulation and analysis results
                if st.session_state.quiz_logger:
                    # Log sample size calculation
                    design_params_dict = {
                        'alpha': st.session_state.scenario_data.design_params.alpha,
                        'power': st.session_state.scenario_data.design_params.power,
                        'baseline_conversion_rate': st.session_state.scenario_data.design_params.baseline_conversion_rate,
                        'target_lift_pct': st.session_state.scenario_data.design_params.target_lift_pct
                    }
                    sample_size_dict = {
                        'per_arm': sample_size_result.per_arm,
                        'total': sample_size_result.total,
                        'days_required': sample_size_result.days_required,
                        'power_achieved': sample_size_result.power_achieved
                    }
                    st.session_state.quiz_logger.log_sample_size_calculation(design_params_dict, sample_size_dict)
                    
                    # Log simulation results
                    sim_dict = {
                        'control_n': sim_result.control_n,
                        'control_conversions': sim_result.control_conversions,
                        'control_rate': sim_result.control_rate,
                        'treatment_n': sim_result.treatment_n,
                        'treatment_conversions': sim_result.treatment_conversions,
                        'treatment_rate': sim_result.treatment_rate,
                        'absolute_lift': sim_result.absolute_lift,
                        'relative_lift_pct': sim_result.relative_lift_pct
                    }
                    st.session_state.quiz_logger.log_simulation_results(sim_dict)
                    
                    # Log analysis results
                    analysis_dict = {
                        'p_value': analysis_result.p_value,
                        'significant': analysis_result.significant,
                        'confidence_interval': str(analysis_result.confidence_interval),
                        'recommendation': analysis_result.recommendation
                    }
                    st.session_state.quiz_logger.log_analysis_results(analysis_dict)
        
        st.markdown("### 📊 Session Progress")
        if st.session_state.scenario_data:
            st.success("✅ Scenario loaded")
        else:
            st.info("ℹ️ No scenario loaded")
        
        if st.session_state.design_scoring_results:
            st.success("✅ Design questions scored")
        
        if st.session_state.simulation_results:
            st.success("✅ Simulation complete")
        
        if st.session_state.analysis_scoring_results:
            st.success("✅ Analysis scored")
        
        st.markdown("### 🎯 Current Step")
        step_colors = {
            "scenario": "🔵",
            "design": "🟡",
            "data_download": "🟢", 
            "analysis": "🟣"
        }
        current_step = st.session_state.current_step
        st.info(f"{step_colors.get(current_step, '⚪')} {current_step.replace('_', ' ').title()}")
        
        # Show scenario specs if available
        if st.session_state.scenario_data:
            # Initialize session state for answers visibility
            if "answers_visible" not in st.session_state:
                st.session_state.answers_visible = False
            
            # Button for showing/hiding answers
            if st.session_state.answers_visible:
                if st.button("🙈 Hide Answers", key="hide_answers_button"):
                    st.session_state.answers_visible = False
                    st.rerun()
            else:
                if st.button("🔍 Show Answers", key="show_answers_button"):
                    st.session_state.answers_visible = True
                    st.rerun()
            
            # Get design parameters for calculations
            scenario = st.session_state.scenario_data.scenario
            design = st.session_state.scenario_data.design_params
            
            if st.session_state.answers_visible:
                st.markdown("### 📋 Scenario Specs")
                
                # Calculate absolute lift in percentage points
                st.markdown(f"**Baseline:** {design.baseline_conversion_rate:.1%}")
                st.markdown(f"**MDE (absolute):** {design.mde_absolute:.1%}")
                st.markdown(f"**Target Relative Lift:** {design.target_lift_pct:.1%}")
                st.markdown(f"**Daily Traffic:** {design.expected_daily_traffic:,}")
                st.markdown(f"**Alpha:** {design.alpha}")
                st.markdown(f"**Power:** {design.power:.1%}")
                
                # Add correct answers for questions 4, 5, 6
                from core.design import compute_sample_size
                from core.types import DesignParams, Allocation
                
                # Calculate correct sample size (Question 4)
                design_params = DesignParams(
                    baseline_conversion_rate=design.baseline_conversion_rate,
                    target_lift_pct=design.target_lift_pct,
                    alpha=design.alpha,
                    power=design.power,
                    allocation=Allocation(0.5, 0.5),
                    expected_daily_traffic=design.expected_daily_traffic
                )
                sample_size_result = compute_sample_size(design_params)
                correct_sample_size = sample_size_result.per_arm
                
                # Calculate correct duration (Question 5)
                required_sample_size = correct_sample_size * 2  # Total sample size
                correct_duration = max(1, round(required_sample_size / design.expected_daily_traffic))
                
                # Calculate correct additional conversions (Question 6)
                correct_additional_conversions = round(design.expected_daily_traffic * design.mde_absolute)
                
                st.markdown("---")
                st.markdown("### 🎯 Design Answers")
                st.markdown(f"**Sample Size (per group):** {correct_sample_size:,}")
                st.markdown(f"**Duration:** {correct_duration} days")
                st.markdown(f"**Additional Conversions/Day:** {correct_additional_conversions}")
                
                # Add simulation results if available
                if st.session_state.simulation_results:
                    sim_result = st.session_state.simulation_results
                    st.markdown("---")
                    st.markdown("### 📊 Actual Results")
                    st.markdown(f"**Control Rate:** {sim_result.control_rate:.3%}")
                    st.markdown(f"**Treatment Rate:** {sim_result.treatment_rate:.3%}")
                    st.markdown(f"**Control Users:** {sim_result.control_n:,}")
                    st.markdown(f"**Treatment Users:** {sim_result.treatment_n:,}")
                    st.markdown(f"**Control Conversions:** {sim_result.control_conversions:,}")
                    st.markdown(f"**Treatment Conversions:** {sim_result.treatment_conversions:,}")
                    
                    # Calculate and display lift metrics using core properties
                    absolute_lift = sim_result.absolute_lift * 100
                    relative_lift = sim_result.relative_lift_pct * 100
                    st.markdown(f"**Absolute Lift:** {absolute_lift:.3f} pp")
                    st.markdown(f"**Relative Lift:** {relative_lift:.1f}%")
                    
                    # Use core analysis for statistical metrics
                    if st.session_state.analysis_results:
                        analysis = st.session_state.analysis_results
                        st.markdown(f"**P-value:** {analysis.p_value:.3f}")
                        ci_lower, ci_upper = analysis.confidence_interval
                        st.markdown(f"**95% CI:** [{ci_lower*100:.2f}%, {ci_upper*100:.2f}%]")
            
            # Navigation buttons
            st.markdown("### 🔄 Navigation")
            if current_step != "scenario":
                if st.button("⬅️ Back to Scenario", key="back_to_scenario_sidebar"):
                    st.session_state.current_step = "scenario"
                    st.rerun()
            
            if current_step == "design" and st.session_state.design_scoring_results:
                if st.button("📊 View Design Results", key="view_design_results"):
                    st.session_state.current_step = "data_download"
                    st.rerun()
    
    # Main content
    if not st.session_state.scenario_data:
        # Hero Section
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 2rem;">
            <h1 style="color: white; font-size: 3rem; margin-bottom: 1rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🧪 30 Day A/Bs</h1>
            <p style="color: white; font-size: 1.3rem; margin-bottom: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Master A/B Testing for Data Science Interviews</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Value Proposition
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 2rem; border-radius: 10px; border-left: 5px solid #28a745; margin-bottom: 1rem;">
            <h2 style="color: #2c3e50; margin-bottom: 1rem;">🎯 Why This Tool?</h2>
            <p style="font-size: 1.1rem; color: #495057; margin-bottom: 1.5rem;">
                A/B testing is one of the most common interview topics for data science roles. 
                This interactive simulator goes beyond static examples by <strong>generating unique business scenarios</strong> with AI, 
                <strong>simulating real experimental datasets</strong>, and providing <strong>Jupyter notebooks</strong> for hands-on analysis - 
                giving you the complete end-to-end experience you might face in a work environment.
            </p>
            <div style="display: flex; justify-content: space-around; text-align: center; margin-top: 1.5rem; margin-bottom: 0;">
                <div style="flex: 1; padding: 0 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                    <div style="font-weight: bold; color: #28a745;">Real Scenarios</div>
                </div>
                <div style="flex: 1; padding: 0 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎓</div>
                    <div style="font-weight: bold; color: #28a745;">Instant Feedback</div>
                </div>
                <div style="flex: 1; padding: 0 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
                    <div style="font-weight: bold; color: #28a745;">Interview Ready</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background-color: #e3f2fd; border-radius: 10px; height: 240px; display: flex; flex-direction: column; position: relative; overflow: hidden;">
                <div style="flex: 0 0 auto; padding-top: 1rem;">
                    <h3 style="color: #1976d2; margin-bottom: 0.5rem;">Read Scenario</h3>
                </div>
                <div style="flex: 1; display: flex; align-items: center; justify-content: center;">
                    <p style="font-size: 0.85rem; color: #424242; line-height: 1.3; margin: 0;">AI-generated realistic business cases with proper statistical parameters</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background-color: #fff3e0; border-radius: 10px; height: 240px; display: flex; flex-direction: column; position: relative; overflow: hidden;">
                <div style="flex: 0 0 auto; padding-top: 1rem;">
                    <h3 style="color: #f57c00; margin-bottom: 0.5rem;">Design Test</h3>
                </div>
                <div style="flex: 1; display: flex; align-items: center; justify-content: center;">
                    <p style="font-size: 0.85rem; color: #424242; line-height: 1.3; margin: 0;">Calculate sample size, MDE, power, and experiment duration</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background-color: #e8f5e8; border-radius: 10px; height: 240px; display: flex; flex-direction: column; position: relative; overflow: hidden;">
                <div style="flex: 0 0 auto; padding-top: 1rem;">
                    <h3 style="color: #388e3c; margin-bottom: 0.5rem;">Analyze Data</h3>
                </div>
                <div style="flex: 1; display: flex; align-items: center; justify-content: center;">
                    <p style="font-size: 0.85rem; color: #424242; line-height: 1.3; margin: 0;">Download CSV data and perform statistical analysis</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background-color: #f3e5f5; border-radius: 10px; height: 240px; display: flex; flex-direction: column; position: relative; overflow: hidden;">
                <div style="flex: 0 0 auto; padding-top: 1rem;">
                    <h3 style="color: #7b1fa2; margin-bottom: 0.5rem;">Get Feedback</h3>
                </div>
                <div style="flex: 1; display: flex; align-items: center; justify-content: center;">
                    <p style="font-size: 0.85rem; color: #424242; line-height: 1.3; margin: 0;">Compare your answers with correct solutions and explanations</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        

        # Call to Action
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin: 2rem 0;">
            <h3 style="color: white; margin-bottom: 1rem;">Ready to Practice?</h3>
            <p style="color: white; font-size: 1.1rem; margin-bottom: 1.5rem;">Generate your first scenario and start mastering A/B testing!</p>
            <div style="font-size: 1.2rem; color: #ffd700;">✨ Click "Generate New Scenario" in the sidebar to begin</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Key Differentiators
        st.markdown("### 🚀 What Makes This Different")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <div style="font-size: 2rem; color: #6f42c1; font-weight: bold;">∞</div>
                <div style="color: #6c757d; font-weight: bold;">Unique Scenarios</div>
                <div style="font-size: 0.9rem; color: #6c757d;">AI-generated realistic business cases</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <div style="font-size: 2rem; color: #007bff; font-weight: bold;">📊</div>
                <div style="color: #6c757d; font-weight: bold;">Real Data</div>
                <div style="font-size: 0.9rem; color: #6c757d;">Simulates actual experimental datasets</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <div style="font-size: 2rem; color: #28a745; font-weight: bold;">⚡</div>
                <div style="color: #6c757d; font-weight: bold;">Instant Feedback</div>
                <div style="font-size: 0.9rem; color: #6c757d;">Immediately understand your results</div>
            </div>
            """, unsafe_allow_html=True)
        
        return
    
    # Step 1: Display scenario
    if st.session_state.current_step == "scenario":
        display_scenario(st.session_state.scenario_data)
        
        if st.button("➡️ Next: Design the Experiment", type="primary"):
            st.session_state.current_step = "design"
            st.rerun()
    
    # Show first design question inline if we're in design step with question 1
    elif st.session_state.current_step == "design":
        # Show scenario first
        display_scenario(st.session_state.scenario_data)
        
        # Add main header and notebook download option
        st.markdown("### 🎯 Design the Experiment")
        st.markdown("Download this Jupyter notebook to work through the calculations for the design questions:")
        create_notebook_download()
        
        st.markdown("---")  # Add separator
        
        # Ensure current_question doesn't exceed maximum
        if st.session_state.current_question > MAX_DESIGN_QUESTIONS:
            st.session_state.current_question = MAX_DESIGN_QUESTIONS
        
        # Show all questions vertically on the same page
        for q_num in range(1, st.session_state.current_question + 1):
            # Check if this question should be shown
            if q_num == 1 or (q_num - 1) in st.session_state.completed_questions:
                ask_single_design_question(q_num)
                st.markdown("---")  # Add separator between questions
            else:
                # Show locked question message
                st.markdown(f"**Question {q_num} of {MAX_DESIGN_QUESTIONS}**")
                st.warning(f"⚠️ Please complete Question {q_num - 1} correctly before proceeding to Question {q_num}")
                st.info("💡 Go back and answer the previous question correctly to unlock this question")
                st.markdown("---")
                break  # Stop showing more questions if one is locked
        
        # Navigation buttons at the bottom
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Back to Scenario", key="back_to_scenario_main"):
                st.session_state.current_step = "scenario"
                st.rerun()
        
        with col2:
            if st.session_state.current_question < MAX_DESIGN_QUESTIONS:
                # Show Next Question button (user can proceed even if current question is wrong)
                if st.button("➡️ Next Question", type="primary"):
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                # For question 6, check if it's completed before allowing submit
                if st.session_state.current_question in st.session_state.completed_questions:
                    if st.button("✅ Submit All Answers", type="primary"):
                        # Score the design answers
                        design_scores, design_total, design_max = score_design_answers(
                            st.session_state.design_answers, 
                            st.session_state.scenario_data, 
                            st.session_state.sample_size_result
                        )
                        st.session_state.design_scoring_results = (design_scores, design_total, design_max)
                        st.session_state.current_step = "data_download"
                        st.rerun()
                else:
                    st.info("💡 Answer the current question correctly to submit all answers")
        
        with col3:
            if st.session_state.current_question > 1 and st.session_state.current_question < MAX_DESIGN_QUESTIONS:
                if st.button("⏭️ Skip", key="skip_question"):
                    st.session_state.current_question += 1
                    st.rerun()
    
    # Step 3: Data download
    elif st.session_state.current_step == "data_download":
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("⬅️ Back", key="back_from_data"):
                st.session_state.current_step = "design"
                st.rerun()
        
        st.markdown("### 🚀 Run the Experiment")
        st.markdown("Great job on the design questions! Now, let's kick off the experiment and gather the data we need to analyze the effect of the updates.")
        
        # Initialize experiment state if not exists
        if 'experiment_started' not in st.session_state:
            st.session_state.experiment_started = False
        if 'experiment_completed' not in st.session_state:
            st.session_state.experiment_completed = False
        
        # Step 1: Start the experiment
        if not st.session_state.experiment_started:
            if st.button("🎯 Start Experiment", type="primary", key="start_experiment"):
                st.session_state.experiment_started = True
                st.rerun()
        
        # Step 2: Show loading animation
        elif st.session_state.experiment_started and not st.session_state.experiment_completed:
            st.markdown("### ⚡ Experiment Running...")
            
            # Create a progress bar with loading animation
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            import time
            
            # Simulate experiment progress
            for i in range(101):
                progress_bar.progress(i)
                if i < 30:
                    status_text.text(f'Setting up test groups... {i}%')
                elif i < 60:
                    status_text.text(f'Collecting user interactions... {i}%')
                elif i < 90:
                    status_text.text(f'Recording conversions... {i}%')
                else:
                    status_text.text(f'Finalizing results... {i}%')
                time.sleep(0.02)  # Small delay for animation effect
            
            # Mark experiment as completed
            st.session_state.experiment_completed = True
            st.rerun()
        
        # Step 3: Show completion and download
        elif st.session_state.experiment_completed:
            st.success("### 🎉 Experiment Complete!")
            st.markdown("Great! The experiment has been run and the data has been captured. Let's analyze the data.")
            
            st.markdown("### 📊 Analyze the Experimental Data")
            st.markdown("Download both the experimental data and analysis template to work through the results:")
            
            if st.session_state.simulation_results:
                # Create two columns for side-by-side downloads
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📊 Experimental Data**")
                    create_csv_download(st.session_state.simulation_results)
                
                with col2:
                    st.markdown("**📓 Analysis Template**")
                    create_analysis_notebook_download()
            
            if st.button("➡️ Next: Analyze the Data", type="primary"):
                st.session_state.current_step = "analysis"
                st.rerun()
    
    # Step 3: Analysis questions
    elif st.session_state.current_step == "analysis":
        st.markdown("### 🔍 Step 3: Analyze the Data")
        st.markdown("Now that you've downloaded the CSV data, let's analyze it step by step:")
        st.markdown("💡 **Tip:** Use the actual results shown in the sidebar to help answer these questions.")
        
        # Ensure current_analysis_question doesn't exceed maximum
        if st.session_state.current_analysis_question > MAX_ANALYSIS_QUESTIONS:
            st.session_state.current_analysis_question = MAX_ANALYSIS_QUESTIONS
        
        # Show all analysis questions vertically on the same page
        for q_num in range(1, st.session_state.current_analysis_question + 1):
            # Check if this question should be shown
            if q_num == 1 or (q_num - 1) in st.session_state.completed_analysis_questions:
                ask_single_analysis_question(q_num)
                st.markdown("---")  # Add separator between questions
            else:
                # Show locked question message
                st.markdown(f"**Question {q_num} of {MAX_ANALYSIS_QUESTIONS}**")
                st.warning(f"⚠️ Please complete Question {q_num - 1} correctly before proceeding to Question {q_num}")
                st.info("💡 Go back and answer the previous question correctly to unlock this question")
                st.markdown("---")
                break  # Stop showing more questions if one is locked
        
        # Navigation buttons at the bottom
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Back to Data Download", key="back_to_data_download"):
                st.session_state.current_step = "data_download"
                st.rerun()
        
        with col2:
            if st.session_state.current_analysis_question < MAX_ANALYSIS_QUESTIONS:
                # Show Next Question button (user can proceed even if current question is wrong)
                if st.button("➡️ Next Question", type="primary"):
                    st.session_state.current_analysis_question += 1
                    st.rerun()
            else:
                # For question 2, check if it's completed before allowing submit
                if st.session_state.current_analysis_question in st.session_state.completed_analysis_questions:
                    if st.button("✅ Complete Analysis", type="primary"):
                        # Score the analysis answers
                        analysis_scores, analysis_total, analysis_max = score_data_analysis_answers(
                            st.session_state.analysis_answers, 
                            st.session_state.simulation_results
                        )
                        st.session_state.analysis_scoring_results = (analysis_scores, analysis_total, analysis_max)
                        st.rerun()
                else:
                    st.info("💡 Answer the current question correctly to complete the analysis")
        
        with col3:
            if st.session_state.current_analysis_question > 1 and st.session_state.current_analysis_question < MAX_ANALYSIS_QUESTIONS:
                if st.button("⏭️ Skip", key="skip_analysis_question"):
                    st.session_state.current_analysis_question += 1
                    st.rerun()
        
        # Display analysis scoring results
        if st.session_state.analysis_scoring_results:
            scores, total_score, max_score = st.session_state.analysis_scoring_results
            display_analysis_scoring_results(scores, total_score, max_score)
            
            st.markdown("### 🎉 Analysis Complete!")
            st.markdown("Great job calculating the conversion rates! Generate a new scenario to practice again, or we'll add more analysis questions soon.")

if __name__ == "__main__":
    main()
