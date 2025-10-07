from dataclasses import dataclass

@dataclass
class Config:
    """System configuration - all tunable parameters in one place."""
    # Privacy
    max_epsilon: float = 10.0
    delta: float = 1e-5
    privacy_sensitivity: float = 1000.0
    privacy_epsilon_per_query: float = 0.01

    # Drift detection
    drift_window_size: int = 100
    drift_threshold: float = 3.0
    drift_mode: str = "diag"  # "diag" or "full" (full requires numpy)

    # System
    min_test_samples: int = 20
    schema_version: str = "1.0.0"
    component_version: str = "0.8.0"

    # Bounds for clipping
    amount_min: float = 0.0
    amount_max: float = 10_000_000.0
