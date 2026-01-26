"""
Data simulation engine for AB testing.

This module generates realistic user-level data based on LLM-expected
conversion rates with proper statistical properties and noise patterns.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List

from .types import DesignParams, SimResult


def simulate_trial(params: DesignParams, seed: int = 42,
                   sample_size_per_arm: int = None,
                   generate_user_data: bool = False) -> SimResult:
    """
    Simulate a complete AB test trial with user-level data.

    This function generates realistic treatment effects that may or may not achieve
    the target lift, allowing for both successful and unsuccessful experiments.

    Args:
        params: Design parameters including allocation and traffic
        seed: Random seed for reproducibility
        sample_size_per_arm: Number of users per arm. If None, uses calculated
                            sample size based on design params (much faster than
                            simulating 30 days of traffic)
        generate_user_data: If True, generates detailed user-level data (slower).
                           If False, only generates aggregate counts (faster).

    Returns:
        SimResult with conversion counts and optionally user-level data

    Raises:
        ValueError: If design parameters are invalid
    """
    # Set random seed for reproducibility
    random.seed(seed)

    # Calculate true rates with realistic variation
    # Control rate varies around baseline due to sampling variability
    # This reflects the reality that observed rates differ from true population rates
    baseline_rate = params.baseline_conversion_rate

    # Add realistic variation to control rate (±10% of baseline)
    control_variation = random.uniform(-0.1, 0.1)  # ±10% variation
    control_rate = baseline_rate * (1 + control_variation)
    control_rate = max(0.001, min(0.999, control_rate))  # Keep within bounds

    # Treatment rate varies around the target lift with realistic uncertainty
    # This allows for both successful and unsuccessful experiments
    # Target: control_rate * (1 + params.target_lift_pct)

    # Add realistic variation to treatment effect
    # 70% chance of achieving target lift, 20% chance of partial success, 10% chance of failure
    effect_variation = random.choices(
        [1.0, 0.5, 0.0, -0.3],  # Full effect, partial effect, no effect, negative effect
        weights=[0.7, 0.2, 0.08, 0.02]  # Probabilities
    )[0]

    # Calculate actual treatment rate with variation
    actual_lift_pct = params.target_lift_pct * effect_variation
    treatment_rate = control_rate * (1 + actual_lift_pct)

    # Ensure treatment rate stays within valid bounds
    treatment_rate = max(0.001, min(0.999, treatment_rate))

    # Validate rates
    if not (0 <= control_rate <= 1 and 0 <= treatment_rate <= 1):
        raise ValueError("Conversion rates must be between 0 and 1")

    # Calculate sample sizes
    if sample_size_per_arm is not None:
        # Use provided sample size
        control_n = sample_size_per_arm
        treatment_n = sample_size_per_arm
    else:
        # Calculate based on design parameters - use calculated sample size for speed
        # Import here to avoid circular imports
        from .design import compute_sample_size
        sample_size_result = compute_sample_size(params)
        control_n = sample_size_result.per_arm
        treatment_n = sample_size_result.per_arm

    if generate_user_data:
        # Generate full user-level data (slower but provides detailed data)
        user_data = _generate_user_data(
            control_n=control_n,
            treatment_n=treatment_n,
            control_rate=control_rate,
            treatment_rate=treatment_rate,
            seed=seed
        )

        # Count conversions from user data
        control_conversions = sum(1 for user in user_data if user['group'] == 'control' and user['converted'])
        treatment_conversions = sum(1 for user in user_data if user['group'] == 'treatment' and user['converted'])
    else:
        # Fast path: just simulate aggregate counts using binomial distribution
        # This is much faster and statistically equivalent
        control_conversions = sum(1 for _ in range(control_n) if random.random() < control_rate)
        treatment_conversions = sum(1 for _ in range(treatment_n) if random.random() < treatment_rate)
        user_data = []  # No detailed user data in fast mode

    return SimResult(
        control_n=control_n,
        control_conversions=control_conversions,
        treatment_n=treatment_n,
        treatment_conversions=treatment_conversions,
        user_data=user_data
    )


def _generate_user_data(control_n: int, treatment_n: int, control_rate: float, 
                       treatment_rate: float, seed: int) -> List[Dict]:
    """
    Generate realistic user-level data with proper statistical properties.
    
    Args:
        control_n: Number of users in control group
        treatment_n: Number of users in treatment group
        control_rate: True conversion rate for control group
        treatment_rate: True conversion rate for treatment group
        seed: Random seed for reproducibility
        
    Returns:
        List of user dictionaries with visitor_id, group, converted, timestamp
    """
    user_data = []
    user_id = 1
    
    # Generate control group data
    for _ in range(control_n):
        converted = random.random() < control_rate
        timestamp = _generate_realistic_timestamp(seed + user_id)
        
        user_data.append({
            'visitor_id': f"user_{user_id:06d}",
            'group': 'control',
            'converted': converted,
            'timestamp': timestamp,
            'session_duration': _generate_session_duration(converted),
            'page_views': _generate_page_views(converted),
            'device_type': _generate_device_type(),
            'traffic_source': _generate_traffic_source()
        })
        user_id += 1
    
    # Generate treatment group data
    for _ in range(treatment_n):
        converted = random.random() < treatment_rate
        timestamp = _generate_realistic_timestamp(seed + user_id)
        
        user_data.append({
            'visitor_id': f"user_{user_id:06d}",
            'group': 'treatment',
            'converted': converted,
            'timestamp': timestamp,
            'session_duration': _generate_session_duration(converted),
            'page_views': _generate_page_views(converted),
            'device_type': _generate_device_type(),
            'traffic_source': _generate_traffic_source()
        })
        user_id += 1
    
    # Shuffle to randomize order
    random.shuffle(user_data)
    
    return user_data


def _generate_realistic_timestamp(seed: int) -> str:
    """
    Generate realistic timestamps with some patterns (business hours, weekdays).
    
    Args:
        seed: Seed for deterministic generation
        
    Returns:
        ISO format timestamp string
    """
    # Use seed to create deterministic but varied timestamps
    random.seed(seed)
    
    # Generate date within last 30 days
    days_ago = random.randint(0, 30)
    date = datetime.now() - timedelta(days=days_ago)
    
    # Bias toward business hours (9 AM - 6 PM) and weekdays
    if random.random() < 0.7:  # 70% chance of weekday
        # Weekday
        hour = random.choices(
            range(24),
            weights=[1, 1, 1, 1, 1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 3, 2, 1, 1, 1, 1]
        )[0]
    else:  # Weekend
        hour = random.randint(10, 22)  # More limited hours
    
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    timestamp = date.replace(hour=hour, minute=minute, second=second)
    return timestamp.isoformat()


def _generate_session_duration(converted: bool) -> int:
    """
    Generate realistic session duration based on conversion status.
    
    Args:
        converted: Whether the user converted
        
    Returns:
        Session duration in seconds
    """
    if converted:
        # Converters tend to have longer sessions
        return random.randint(300, 1800)  # 5-30 minutes
    else:
        # Non-converters have shorter sessions
        return random.randint(30, 600)  # 30 seconds - 10 minutes


def _generate_page_views(converted: bool) -> int:
    """
    Generate realistic page views based on conversion status.
    
    Args:
        converted: Whether the user converted
        
    Returns:
        Number of page views
    """
    if converted:
        # Converters view more pages
        return random.randint(3, 15)
    else:
        # Non-converters view fewer pages
        return random.randint(1, 5)


def _generate_device_type() -> str:
    """
    Generate realistic device type distribution.
    
    Returns:
        Device type string
    """
    return random.choices(
        ['desktop', 'mobile', 'tablet'],
        weights=[0.4, 0.5, 0.1]
    )[0]


def _generate_traffic_source() -> str:
    """
    Generate realistic traffic source distribution.
    
    Returns:
        Traffic source string
    """
    return random.choices(
        ['organic', 'direct', 'social', 'paid', 'email', 'referral'],
        weights=[0.35, 0.25, 0.15, 0.15, 0.05, 0.05]
    )[0]


def validate_simulation_consistency(sim_result: SimResult, expected_rates: Dict[str, float], 
                                  tolerance: float = 0.05) -> bool:
    """
    Validate that simulated data produces expected conversion rates within tolerance.
    
    Args:
        sim_result: Simulation results
        expected_rates: Expected conversion rates
        tolerance: Acceptable deviation from expected rates
        
    Returns:
        True if simulation is consistent with expectations
    """
    expected_control = expected_rates.get('control', 0)
    expected_treatment = expected_rates.get('treatment', 0)
    
    actual_control = sim_result.control_rate
    actual_treatment = sim_result.treatment_rate
    
    control_diff = abs(actual_control - expected_control)
    treatment_diff = abs(actual_treatment - expected_treatment)
    
    return control_diff <= tolerance and treatment_diff <= tolerance


def add_seasonality_pattern(user_data: List[Dict], pattern_type: str = "weekend") -> List[Dict]:
    """
    Add realistic seasonality patterns to user data.
    
    Args:
        user_data: List of user dictionaries
        pattern_type: Type of seasonality pattern
        
    Returns:
        Modified user data with seasonality effects
    """
    if pattern_type == "weekend":
        # Weekend users have different conversion patterns
        for user in user_data:
            timestamp = datetime.fromisoformat(user['timestamp'])
            if timestamp.weekday() >= 5:  # Weekend
                # Slightly lower conversion rates on weekends
                if user['converted'] and random.random() < 0.1:
                    user['converted'] = False
    
    elif pattern_type == "holiday":
        # Holiday effect (simplified)
        for user in user_data:
            timestamp = datetime.fromisoformat(user['timestamp'])
            # Simulate holiday effect (e.g., Black Friday)
            if random.random() < 0.05:  # 5% chance of holiday effect
                if not user['converted'] and random.random() < 0.2:
                    user['converted'] = True
    
    return user_data


def export_user_data_csv(user_data: List[Dict], filename: str) -> None:
    """
    Export user-level data to CSV file.
    
    Args:
        user_data: List of user dictionaries
        filename: Output filename
    """
    import csv
    
    if not user_data:
        return
    
    fieldnames = user_data[0].keys()
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(user_data)


def get_aggregate_summary(user_data: List[Dict]) -> Dict:
    """
    Generate aggregate summary statistics from user-level data.
    
    Args:
        user_data: List of user dictionaries
        
    Returns:
        Dictionary with summary statistics
    """
    if not user_data:
        return {}
    
    # Group by treatment group
    control_users = [u for u in user_data if u['group'] == 'control']
    treatment_users = [u for u in user_data if u['group'] == 'treatment']
    
    summary = {
        'total_users': len(user_data),
        'control': {
            'count': len(control_users),
            'conversions': sum(1 for u in control_users if u['converted']),
            'conversion_rate': sum(1 for u in control_users if u['converted']) / len(control_users) if control_users else 0,
            'avg_session_duration': sum(u['session_duration'] for u in control_users) / len(control_users) if control_users else 0,
            'avg_page_views': sum(u['page_views'] for u in control_users) / len(control_users) if control_users else 0
        },
        'treatment': {
            'count': len(treatment_users),
            'conversions': sum(1 for u in treatment_users if u['converted']),
            'conversion_rate': sum(1 for u in treatment_users if u['converted']) / len(treatment_users) if treatment_users else 0,
            'avg_session_duration': sum(u['session_duration'] for u in treatment_users) / len(treatment_users) if treatment_users else 0,
            'avg_page_views': sum(u['page_views'] for u in treatment_users) / len(treatment_users) if treatment_users else 0
        }
    }
    
    # Calculate lift metrics
    control_rate = summary['control']['conversion_rate']
    treatment_rate = summary['treatment']['conversion_rate']
    
    if control_rate > 0:
        summary['absolute_lift'] = treatment_rate - control_rate
        summary['relative_lift_pct'] = (treatment_rate - control_rate) / control_rate * 100
    else:
        summary['absolute_lift'] = 0
        summary['relative_lift_pct'] = 0
    
    return summary
