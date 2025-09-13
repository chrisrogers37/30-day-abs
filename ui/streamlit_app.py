#!/usr/bin/env python3
"""
Streamlit app for 30 Day ABs - AB Test Interview Practice.

This app allows users to:
1. Generate realistic AB test scenarios
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
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging for Streamlit app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import our modules
from llm.client import create_llm_client
from llm.parser import LLMOutputParser
from llm.guardrails import LLMGuardrails
from core.simulate import simulate_trial, export_user_data_csv
from core.analyze import analyze_results
from core.design import compute_sample_size
from core.types import DesignParams, Allocation
from schemas.scenario import ScenarioResponseDTO

# Page configuration
st.set_page_config(
    page_title="30 Day ABs",
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
    if 'sizing_answers' not in st.session_state:
        st.session_state.sizing_answers = {}
    if 'analysis_answers' not in st.session_state:
        st.session_state.analysis_answers = {}
    if 'completed_questions' not in st.session_state:
        st.session_state.completed_questions = set()
    if 'sizing_scoring_results' not in st.session_state:
        st.session_state.sizing_scoring_results = None
    if 'analysis_scoring_results' not in st.session_state:
        st.session_state.analysis_scoring_results = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "scenario"  # scenario -> design -> data_download -> sizing -> analysis
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 1  # Track which design question we're on
    if 'design_answers' not in st.session_state:
        st.session_state.design_answers = {}  # Store answers as we go

def generate_scenario():
    """Generate a new AB test scenario."""
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
            
            # True rates from LLM simulation hints
            simulation_hints = scenario_dto.llm_expected.simulation_hints
            true_rates = {
                "control": simulation_hints.control_conversion_rate,
                "treatment": simulation_hints.treatment_conversion_rate
            }
            
            logger.info(f"🎯 True rates - Control: {true_rates['control']:.3f}, Treatment: {true_rates['treatment']:.3f}")
            
            # Calculate sample size
            logger.info("📏 Calculating required sample size...")
            sample_size_result = compute_sample_size(core_design_params)
            
            # Run simulation
            logger.info("🔄 Running simulation with seed=42...")
            sim_result = simulate_trial(core_design_params, true_rates, seed=42)
            
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
    
    # Design parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Baseline Rate", f"{design.baseline_conversion_rate:.1%}")
        st.metric("MDE (absolute)", f"{design.mde_absolute:.1%}")
        st.metric("Target Relative Lift", f"{design.target_lift_pct:.1%}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Alpha", f"{design.alpha}")
        st.metric("Power", f"{design.power}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Daily Traffic", f"{design.expected_daily_traffic:,}")
        st.metric("Allocation", f"{design.allocation.control:.0%} / {design.allocation.treatment:.0%}")
        st.markdown('</div>', unsafe_allow_html=True)

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

def validate_question_answer(question_num, user_answer):
    """Validate a single question answer and return feedback."""
    if not st.session_state.scenario_data:
        return None, None
    
    design = st.session_state.scenario_data.design_params
    baseline = design.baseline_conversion_rate
    target_lift = design.target_lift_pct
    
    if question_num == 1:
        # Question 1: Relative lift calculation from MDE
        mde_absolute = design.mde_absolute  # MDE in absolute terms from scenario
        correct_answer = (mde_absolute / baseline) * 100  # Convert to relative lift percentage
        tolerance = 2.0  # 2% tolerance for relative lift
        is_correct = abs(user_answer - correct_answer) <= tolerance
        return is_correct, f"Correct answer: {correct_answer:.1f}%"
    
    elif question_num == 2:
        # Question 2: Sample size calculation
        from core.design import compute_sample_size
        from core.types import DesignParams, Allocation
        
        # Create DesignParams object
        design_params = DesignParams(
            baseline_conversion_rate=baseline,
            target_lift_pct=target_lift,
            alpha=design.alpha,
            power=design.power,
            allocation=Allocation(0.5, 0.5),
            expected_daily_traffic=design.expected_daily_traffic
        )
        
        sample_size_result = compute_sample_size(design_params)
        correct_sample_size = sample_size_result.per_arm
        tolerance = 100  # 100 users tolerance to account for calculator differences
        is_correct = abs(user_answer - correct_sample_size) <= tolerance
        return is_correct, f"Correct answer: {correct_sample_size:,} users per group (±{tolerance} tolerance for calculator differences)"
    
    elif question_num == 3:
        # Question 3: Experiment duration
        daily_traffic = design.expected_daily_traffic
        # Calculate required sample size for correct duration
        from core.design import compute_sample_size
        from core.types import DesignParams, Allocation
        
        # Create DesignParams object
        design_params = DesignParams(
            baseline_conversion_rate=baseline,
            target_lift_pct=target_lift,
            alpha=design.alpha,
            power=design.power,
            allocation=Allocation(0.5, 0.5),
            expected_daily_traffic=design.expected_daily_traffic
        )
        
        sample_size_result = compute_sample_size(design_params)
        required_sample_size = sample_size_result.per_arm * 2  # Total sample size
        correct_duration = max(1, round(required_sample_size / daily_traffic))
        tolerance = 2  # 2 days tolerance
        is_correct = abs(user_answer - correct_duration) <= tolerance
        return is_correct, f"Correct answer: {correct_duration} days"
    
    return None, None

def ask_single_design_question(question_num):
    """Ask a single design question based on question number."""
    st.markdown(f"**Question {question_num} of 5**")
    
    if question_num == 1:
        # Question 1: Relative lift calculation from MDE
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
            is_correct, correct_answer = validate_question_answer(1, relative_lift_pct)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_questions.add(1)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Try again: (MDE / Baseline rate) × 100%")
    
    elif question_num == 2:
        # Question 2: Sample size calculation
        if "scenario_data" not in st.session_state or not st.session_state.scenario_data:
            st.error("❌ No scenario available. Please generate a scenario first.")
            return
        scenario = st.session_state.scenario_data
        design = scenario.design_params
        st.markdown(f"**Based on the baseline rate and a target alpha of {design.alpha} and power of {design.power}, how large of a sample size would we need to detect the target effect?**")
        
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
            is_correct, correct_answer = validate_question_answer(2, sample_size)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_questions.add(2)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Use two-proportion z-test sample size formula")
    
    elif question_num == 3:
        # Question 3: Experiment duration
        st.markdown("**How long should this experiment run based on the daily traffic and required sample size?**")
        st.markdown("*Hint: Calculate based on daily traffic and the sample size you calculated*")
        duration_days = st.number_input(
            "Duration (days):",
            min_value=1,
            max_value=365,
            value=st.session_state.design_answers.get("experiment_duration_days", None),
            step=1,
            key="duration_input"
        )
        st.session_state.design_answers["experiment_duration_days"] = duration_days
        
        # Validate and show feedback
        if duration_days is not None:
            is_correct, correct_answer = validate_question_answer(3, duration_days)
            if is_correct is not None:
                if is_correct:
                    st.success(f"✅ Correct! {correct_answer}")
                    st.session_state.completed_questions.add(3)
                else:
                    st.error(f"❌ Incorrect. {correct_answer}")
                    st.info("💡 Calculate: Required sample size ÷ Daily traffic")
    
    elif question_num == 4:
        # Question 4: Business Impact Calculation
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
    
    elif question_num == 5:
        # Question 5: Power Analysis
        st.markdown("**Is 80% statistical power sufficient for this business decision?**")
        power_sufficient = st.selectbox(
            "Choose the best answer:",
            [
                "Yes, 80% is standard and sufficient for most business decisions",
                "No, we should use 90% power for important business decisions",
                "It depends on the business risk tolerance and cost of the experiment",
                "Power doesn't matter for business decisions, only statistical significance"
            ],
            key="power_sufficient_input"
        )
        st.session_state.design_answers["power_sufficient"] = power_sufficient

def ask_experiment_sizing_questions():
    """Ask experiment sizing questions first."""
    st.markdown("### 🎯 Experiment Sizing Questions")
    st.markdown("Based on the scenario above, answer these sizing questions:")
    
    questions = {
        "baseline_rate": "What is the baseline conversion rate? (round to 3 decimal places)",
        "target_lift": "What is the target lift (MDE) for this experiment? (round to 3 decimal places)",
        "alpha": "What significance level (α) should be used? (round to 3 decimal places)",
        "power": "What statistical power is desired? (round to 3 decimal places)",
        "daily_traffic": "What is the expected daily traffic? (integer)",
        "sample_size_per_arm": "What sample size per arm is needed? (integer)"
    }
    
    answers = {}
    
    for key, question in questions.items():
        st.markdown(f'<div class="question-box">', unsafe_allow_html=True)
        st.markdown(f"**Q: {question}**")
        
        if key in ["baseline_rate", "target_lift", "alpha", "power"]:
            answer = st.text_input(f"Answer for {key}:", key=f"input_{key}", placeholder="e.g., 0.025")
        elif key in ["daily_traffic", "sample_size_per_arm"]:
            answer = st.text_input(f"Answer for {key}:", key=f"input_{key}", placeholder="e.g., 10000")
        
        answers[key] = answer
        st.markdown('</div>', unsafe_allow_html=True)
    
    return answers

def ask_analysis_questions():
    """Ask analysis questions after seeing the data."""
    st.markdown("### 🤔 Data Analysis Questions")
    st.markdown("After analyzing the simulated data, answer these questions:")
    
    questions = {
        "p_value": "What is the p-value for this test? (round to 3 decimal places)",
        "significant": "Is the result statistically significant at α=0.05? (yes/no)",
        "business_impact": "What is the business impact of this result? (high/medium/low)",
        "recommendation": "What is your recommendation for next steps? (rollout/do_not_rollout/inconclusive)",
        "sample_size_adequate": "Is the sample size adequate for this test? (yes/no)",
        "power_achieved": "What is the achieved power? (round to 3 decimal places)"
    }
    
    answers = {}
    
    for key, question in questions.items():
        st.markdown(f'<div class="question-box">', unsafe_allow_html=True)
        st.markdown(f"**Q: {question}**")
        
        if key in ["p_value", "power_achieved"]:
            answer = st.text_input(f"Answer for {key}:", key=f"input_{key}", placeholder="e.g., 0.045")
        elif key in ["significant", "sample_size_adequate"]:
            answer = st.selectbox(f"Answer for {key}:", ["", "yes", "no"], key=f"input_{key}")
        elif key == "business_impact":
            answer = st.selectbox(f"Answer for {key}:", ["", "high", "medium", "low"], key=f"input_{key}")
        elif key == "recommendation":
            answer = st.selectbox(f"Answer for {key}:", ["", "rollout", "do_not_rollout", "inconclusive"], key=f"input_{key}")
        
        answers[key] = answer
        st.markdown('</div>', unsafe_allow_html=True)
    
    return answers

def score_sizing_answers(user_answers, scenario_dto):
    """Score sizing questions against scenario parameters."""
    logger.info("🎯 Starting sizing answers scoring...")
    scores = {}
    total_score = 0
    max_score = len(user_answers)
    
    design = scenario_dto.design_params
    
    # Correct answers from scenario
    correct_answers = {
        "baseline_rate": round(design.baseline_conversion_rate, 3),
        "target_lift": round(design.target_lift_pct, 3),
        "alpha": round(design.alpha, 3),
        "power": round(design.power, 3),
        "daily_traffic": design.expected_daily_traffic,
        "sample_size_per_arm": 0  # Will be calculated
    }
    
    # Calculate correct sample size
    from core.design import compute_sample_size
    from core.types import Allocation
    allocation = Allocation(control=design.allocation.control, treatment=design.allocation.treatment)
    core_design = DesignParams(
        baseline_conversion_rate=design.baseline_conversion_rate,
        target_lift_pct=design.target_lift_pct,
        alpha=design.alpha,
        power=design.power,
        allocation=allocation,
        expected_daily_traffic=design.expected_daily_traffic
    )
    sample_size = compute_sample_size(core_design)
    correct_answers["sample_size_per_arm"] = sample_size.per_arm
    
    for key, user_answer in user_answers.items():
        correct_answer = correct_answers[key]
        
        if key in ["baseline_rate", "target_lift", "alpha", "power"]:
            try:
                user_val = round(float(user_answer), 3)
                correct_val = correct_answer
                if abs(user_val - correct_val) < 0.001:
                    scores[key] = {"correct": True, "user": user_answer, "correct": correct_answer}
                    total_score += 1
                else:
                    scores[key] = {"correct": False, "user": user_answer, "correct": correct_answer}
            except:
                scores[key] = {"correct": False, "user": user_answer, "correct": correct_answer}
        elif key in ["daily_traffic", "sample_size_per_arm"]:
            try:
                user_val = int(user_answer)
                correct_val = correct_answer
                if abs(user_val - correct_val) <= 100:  # Allow some tolerance for sample size
                    scores[key] = {"correct": True, "user": user_answer, "correct": correct_answer}
                    total_score += 1
                else:
                    scores[key] = {"correct": False, "user": user_answer, "correct": correct_answer}
            except:
                scores[key] = {"correct": False, "user": user_answer, "correct": correct_answer}
    
    logger.info(f"📊 Sizing scoring complete: {total_score}/{max_score} correct")
    return scores, total_score, max_score

def score_analysis_answers(user_answers, correct_analysis, sim_result):
    """Score analysis questions against correct analysis."""
    logger.info("🔍 Starting analysis answers scoring...")
    scores = {}
    total_score = 0
    max_score = len(user_answers)
    
    # Correct answers
    correct_answers = {
        "p_value": round(correct_analysis.p_value, 6),
        "significant": "yes" if correct_analysis.significant else "no",
        "business_impact": "high" if sim_result.relative_lift_pct > 10 else "medium" if sim_result.relative_lift_pct > 5 else "low",
        "recommendation": "rollout" if correct_analysis.significant and sim_result.relative_lift_pct > 5 else "do_not_rollout" if correct_analysis.significant and sim_result.relative_lift_pct < 0 else "inconclusive",
        "sample_size_adequate": "yes" if sim_result.control_n > 1000 and sim_result.treatment_n > 1000 else "no",
        "power_achieved": round(correct_analysis.power_achieved, 3)
    }
    
    for key, user_answer in user_answers.items():
        correct_answer = correct_answers[key]
        
        if key in ["p_value", "power_achieved"]:
            try:
                user_val = round(float(user_answer), 3)
                correct_val = correct_answer
                if abs(user_val - correct_val) < 0.001:
                    scores[key] = {"correct": True, "user": user_answer, "correct": correct_answer}
                    total_score += 1
                else:
                    scores[key] = {"correct": False, "user": user_answer, "correct": correct_answer}
            except:
                scores[key] = {"correct": False, "user": user_answer, "correct": correct_answer}
        else:
            if user_answer.lower() == correct_answer.lower():
                scores[key] = {"correct": True, "user": user_answer, "correct": correct_answer}
                total_score += 1
            else:
                scores[key] = {"correct": False, "user": user_answer, "correct": correct_answer}
    
    logger.info(f"📊 Analysis scoring complete: {total_score}/{max_score} correct")
    return scores, total_score, max_score

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
    
    st.markdown("### 📝 Detailed Feedback")
    
    for key, result in scores.items():
        if result["correct"]:
            st.success(f"✅ **{key.replace('_', ' ').title()}**: {result['user']} (Correct!)")
        else:
            st.error(f"❌ **{key.replace('_', ' ').title()}**: {result['user']} (Correct answer: {result['correct']})")

def score_design_answers(user_answers, scenario_data, sample_size_result):
    """Score the design questions against correct values"""
    logger.info("🎯 Starting design answers scoring...")
    st.markdown("### 📊 Design Results")
    
    # Calculate correct answers
    correct_sample_size = sample_size_result.per_arm
    correct_duration = max(1, round(correct_sample_size * 2 / scenario_data.design_params.expected_daily_traffic))
    
    # Calculate absolute lift in percentage points
    baseline = scenario_data.design_params.baseline_conversion_rate
    target_lift = scenario_data.design_params.target_lift_pct
    correct_absolute_lift = round(baseline * target_lift * 100, 1)  # Convert to percentage points
    
    # Calculate additional conversions per day
    daily_traffic = scenario_data.design_params.expected_daily_traffic
    correct_additional_conversions = round(daily_traffic * (baseline * target_lift))
    
    # Correct multiple choice answer
    correct_power_sufficient = "It depends on the business risk tolerance and cost of the experiment"
    
    scores = {}
    total_score = 0
    max_score = 6
    
    # Question 1: Target treatment conversion rate
    correct_treatment_rate = (baseline + (baseline * target_lift)) * 100  # Convert to percentage
    user_treatment_rate = user_answers.get("target_treatment_rate", 0)
    if abs(user_treatment_rate - correct_treatment_rate) <= 0.5:  # Allow 0.5% tolerance
        st.success(f"✅ Target treatment rate: {user_treatment_rate:.1f}% (Correct: {correct_treatment_rate:.1f}%)")
        scores["target_treatment_rate"] = {"correct": True, "user": user_treatment_rate, "correct": correct_treatment_rate}
        total_score += 1
    else:
        st.error(f"❌ Target treatment rate: {user_treatment_rate:.1f}% (Correct: {correct_treatment_rate:.1f}%)")
        scores["target_treatment_rate"] = {"correct": False, "user": user_treatment_rate, "correct": correct_treatment_rate}
    
    # Question 2: Duration
    user_duration = user_answers.get("experiment_duration_days", 0)
    if abs(user_duration - correct_duration) <= 2:  # Allow 2 days tolerance
        st.success(f"✅ Duration: {user_duration} days (Correct: {correct_duration} days)")
        scores["duration"] = {"correct": True, "user": user_duration, "correct": correct_duration}
        total_score += 1
    else:
        st.error(f"❌ Duration: {user_duration} days (Correct: {correct_duration} days)")
        scores["duration"] = {"correct": False, "user": user_duration, "correct": correct_duration}
    
    # Question 3: Absolute lift
    user_absolute_lift = user_answers.get("absolute_lift_pp", 0)
    if abs(user_absolute_lift - correct_absolute_lift) <= 0.5:  # Allow 0.5pp tolerance
        st.success(f"✅ Absolute lift: {user_absolute_lift}pp (Correct: {correct_absolute_lift}pp)")
        scores["absolute_lift"] = {"correct": True, "user": user_absolute_lift, "correct": correct_absolute_lift}
        total_score += 1
    else:
        st.error(f"❌ Absolute lift: {user_absolute_lift}pp (Correct: {correct_absolute_lift}pp)")
        scores["absolute_lift"] = {"correct": False, "user": user_absolute_lift, "correct": correct_absolute_lift}
    
    # Question 4: Power sufficient
    user_power_sufficient = user_answers.get("power_sufficient", "")
    if user_power_sufficient == correct_power_sufficient:
        st.success(f"✅ Power analysis: Correct!")
        scores["power_sufficient"] = {"correct": True, "user": user_power_sufficient, "correct": correct_power_sufficient}
        total_score += 1
    else:
        st.error(f"❌ Power analysis: {user_power_sufficient}")
        st.info(f"💡 Correct answer: {correct_power_sufficient}")
        scores["power_sufficient"] = {"correct": False, "user": user_power_sufficient, "correct": correct_power_sufficient}
    
    # Question 5: Additional conversions
    user_additional_conversions = user_answers.get("additional_conversions_per_day", 0)
    if abs(user_additional_conversions - correct_additional_conversions) <= 10:  # Allow 10 conversions tolerance
        st.success(f"✅ Additional conversions: {user_additional_conversions:,}/day (Correct: {correct_additional_conversions:,}/day)")
        scores["additional_conversions"] = {"correct": True, "user": user_additional_conversions, "correct": correct_additional_conversions}
        total_score += 1
    else:
        st.error(f"❌ Additional conversions: {user_additional_conversions:,}/day (Correct: {correct_additional_conversions:,}/day)")
        scores["additional_conversions"] = {"correct": False, "user": user_additional_conversions, "correct": correct_additional_conversions}
    
    # Question 6: Sample size
    user_sample_size = user_answers.get("sample_size_per_group", 0)
    if abs(user_sample_size - correct_sample_size) <= 50:  # Allow some tolerance
        st.success(f"✅ Sample size: {user_sample_size:,} (Correct: {correct_sample_size:,})")
        scores["sample_size"] = {"correct": True, "user": user_sample_size, "correct": correct_sample_size}
        total_score += 1
    else:
        st.error(f"❌ Sample size: {user_sample_size:,} (Correct: {correct_sample_size:,})")
        scores["sample_size"] = {"correct": False, "user": user_sample_size, "correct": correct_sample_size}
    
    percentage = (total_score / max_score) * 100
    st.markdown(f"**Score: {total_score}/{max_score} ({percentage:.1f}%)**")
    
    logger.info(f"📊 Design scoring complete: {total_score}/{max_score} correct")
    return scores, total_score, max_score

def main():
    """Main Streamlit app."""
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">30 Day ABs</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Practice Session")
        
        if st.button("🔄 Generate New Scenario", type="primary"):
            st.session_state.scenario_data = generate_scenario()
            if st.session_state.scenario_data:
                st.session_state.design_answers = {}
                st.session_state.design_scoring_results = None
                st.session_state.current_question = 1  # Reset to first question
                st.session_state.completed_questions = set()  # Reset completed questions
                st.session_state.sizing_answers = {}
                st.session_state.analysis_answers = {}
                st.session_state.sizing_scoring_results = None
                st.session_state.analysis_scoring_results = None
                st.session_state.current_step = "scenario"
                
                # Run simulation and analysis immediately after scenario generation
                sim_result, analysis_result, sample_size_result = run_simulation(st.session_state.scenario_data)
                st.session_state.simulation_results = sim_result
                st.session_state.analysis_results = analysis_result
                st.session_state.sample_size_result = sample_size_result
        
        st.markdown("### 📊 Session Progress")
        if st.session_state.scenario_data:
            st.success("✅ Scenario loaded")
        else:
            st.info("ℹ️ No scenario loaded")
        
        if st.session_state.design_scoring_results:
            st.success("✅ Design questions scored")
        
        if st.session_state.sizing_scoring_results:
            st.success("✅ Sizing questions scored")
        
        if st.session_state.simulation_results:
            st.success("✅ Simulation complete")
        
        if st.session_state.analysis_scoring_results:
            st.success("✅ Analysis scored")
        
        st.markdown("### 🎯 Current Step")
        step_colors = {
            "scenario": "🔵",
            "design": "🟡",
            "data_download": "🟢", 
            "sizing": "🟠",
            "analysis": "🟣"
        }
        current_step = st.session_state.current_step
        st.info(f"{step_colors.get(current_step, '⚪')} {current_step.replace('_', ' ').title()}")
        
        # Show scenario specs if available
        if st.session_state.scenario_data:
            st.markdown("### 📋 Scenario Specs")
            scenario = st.session_state.scenario_data.scenario
            design = st.session_state.scenario_data.design_params
            
            # Calculate absolute lift in percentage points
            st.markdown(f"**Baseline:** {design.baseline_conversion_rate:.1%}")
            st.markdown(f"**MDE (absolute):** {design.mde_absolute:.1%}")
            st.markdown(f"**Target Relative Lift:** {design.target_lift_pct:.1%}")
            st.markdown(f"**Daily Traffic:** {design.expected_daily_traffic:,}")
            st.markdown(f"**Alpha:** {design.alpha}")
            st.markdown(f"**Power:** {design.power:.1%}")
            
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
        st.markdown("### 👋 Welcome to 30 Day ABs!")
        st.markdown("""
        This tool helps you practice AB test analysis for interviews by:
        
        1. **Reading the experiment case** - AI-generated realistic scenarios
        2. **Sizing the experiment** - Calculate sample size, MDE, power
        3. **Analyzing the data** - Download CSV and run your own analysis
        4. **Getting scored feedback** - Compare your answers to correct ones
        
        Click "Generate New Scenario" in the sidebar to get started!
        """)
        
        st.markdown("### 🎯 What You'll Practice")
        st.markdown("""
        - **Experiment sizing** (sample size, MDE, power calculations)
        - **Statistical significance testing** (p-values, confidence intervals)
        - **Business interpretation** (lift, revenue impact)
        - **Decision making** (rollout recommendations)
        """)
        
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
        st.markdown("---")  # Add separator
        
        # Show all questions vertically on the same page
        for q_num in range(1, st.session_state.current_question + 1):
            # Check if this question should be shown
            if q_num == 1 or (q_num - 1) in st.session_state.completed_questions:
                ask_single_design_question(q_num)
                st.markdown("---")  # Add separator between questions
            else:
                # Show locked question message
                st.markdown(f"### 🎯 Step 2: Design the Experiment")
                st.markdown(f"**Question {q_num} of 5**")
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
            if st.session_state.current_question < 5:
                # Show Next Question button (user can proceed even if current question is wrong)
                if st.button("➡️ Next Question", type="primary"):
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                # For question 5, check if it's completed before allowing submit
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
            if st.session_state.current_question > 1:
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
        
        st.markdown("### 📊 Download Simulated Data")
        st.markdown("Great job on the design questions! Now you can download the data and run your own analysis.")
        
        if st.session_state.simulation_results:
            create_csv_download(st.session_state.simulation_results)
        
        if st.button("➡️ Next: Analyze the Data", type="primary"):
            st.session_state.current_step = "sizing"
            st.rerun()
    
    # Step 4: Sizing questions (renamed from Step 2)
    elif st.session_state.current_step == "sizing":
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("⬅️ Back", key="back_from_sizing"):
                st.session_state.current_step = "data_download"
                st.rerun()
        
        st.markdown("### 🎯 Step 4: Size the Experiment")
        st.markdown("Based on the scenario above, answer these sizing questions:")
        
        sizing_answers = ask_experiment_sizing_questions()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back to Data", type="secondary"):
                st.session_state.current_step = "data_download"
                st.rerun()
        
        with col2:
            if st.button("📊 Score Sizing Answers", type="primary"):
                if all(sizing_answers.values()):
                    scores, total_score, max_score = score_sizing_answers(
                        sizing_answers, 
                        st.session_state.scenario_data
                    )
                    st.session_state.sizing_scoring_results = (scores, total_score, max_score)
                    st.session_state.sizing_answers = sizing_answers
                    st.rerun()
                else:
                    st.warning("⚠️ Please answer all questions before scoring.")
        
        # Display sizing scoring results
        if st.session_state.sizing_scoring_results:
            scores, total_score, max_score = st.session_state.sizing_scoring_results
            display_scoring_results(scores, total_score, max_score)
            
            if st.button("➡️ Next: View Simulated Data", type="primary"):
                st.session_state.current_step = "data"
                st.rerun()
    
    # Step 3: Run simulation and show data
    elif st.session_state.current_step == "data":
        st.markdown("### 📊 Step 3: View Simulated Data")
        
        # Run simulation if not already done
        if not st.session_state.simulation_results:
            if st.button("🚀 Run Simulation", type="primary"):
                sim_result, analysis = run_simulation(st.session_state.scenario_data)
                if sim_result and analysis:
                    st.session_state.simulation_results = sim_result
                    st.session_state.analysis_results = analysis
                    st.rerun()
        
        # Display simulation results
        if st.session_state.simulation_results and st.session_state.analysis_results:
            display_simulation_results(st.session_state.simulation_results, st.session_state.analysis_results)
            
            # CSV download
            create_csv_download(st.session_state.simulation_results)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Back to Sizing", type="secondary"):
                    st.session_state.current_step = "sizing"
                    st.rerun()
            
            with col2:
                if st.button("➡️ Next: Analyze Data", type="primary"):
                    st.session_state.current_step = "analysis"
                    st.rerun()
    
    # Step 5: Analysis questions
    elif st.session_state.current_step == "analysis":
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("⬅️ Back", key="back_from_analysis"):
                st.session_state.current_step = "sizing"
                st.rerun()
        
        st.markdown("### 🤔 Step 5: Analyze the Data")
        st.markdown("After analyzing the simulated data, answer these questions:")
        
        analysis_answers = ask_analysis_questions()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back to Sizing", type="secondary"):
                st.session_state.current_step = "sizing"
                st.rerun()
        
        with col2:
            if st.button("📊 Score Analysis Answers", type="primary"):
                if all(analysis_answers.values()):
                    scores, total_score, max_score = score_analysis_answers(
                        analysis_answers, 
                        st.session_state.analysis_results, 
                        st.session_state.simulation_results
                    )
                    st.session_state.analysis_scoring_results = (scores, total_score, max_score)
                    st.session_state.analysis_answers = analysis_answers
                    st.rerun()
                else:
                    st.warning("⚠️ Please answer all questions before scoring.")
        
        # Display analysis scoring results
        if st.session_state.analysis_scoring_results:
            scores, total_score, max_score = st.session_state.analysis_scoring_results
            display_scoring_results(scores, total_score, max_score)
            
            st.markdown("### 🎉 Practice Session Complete!")
            st.markdown("You've completed the full AB test analysis workflow. Generate a new scenario to practice again!")

if __name__ == "__main__":
    main()
