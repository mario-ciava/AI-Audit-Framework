import math, time, secrets
from collections import defaultdict
from typing import Any, Dict, Optional
from .config import Config

class PrivacyAccountant:
    """Real privacy budget accounting (epsilon-DP with Laplace noise)."""
    def __init__(self, config: Config):
        self.config = config
        self.max_epsilon = config.max_epsilon
        self.delta = config.delta
        self.spent_epsilon = 0.0
        self.query_log = []
        self.epsilon_by_category = defaultdict(float)

    def can_query(self, epsilon_cost: float) -> bool:
        return self.spent_epsilon + epsilon_cost <= self.max_epsilon

    def spend(self, epsilon_cost: float, query_type: str) -> bool:
        if not self.can_query(epsilon_cost):
            return False
        self.spent_epsilon += epsilon_cost
        self.epsilon_by_category[query_type] += epsilon_cost
        self.query_log.append({
            "timestamp": time.time(),
            "type": query_type,
            "epsilon": epsilon_cost,
            "total_spent": self.spent_epsilon
        })
        return True

    def remaining_budget(self) -> float:
        return max(0.0, self.max_epsilon - self.spent_epsilon)

    def add_laplace_noise(self, value: float, sensitivity: float, epsilon: float) -> Optional[float]:
        if not self.spend(epsilon, "laplace_query"):
            return None
        scale = sensitivity / epsilon
        u = secrets.SystemRandom().random() - 0.5  # (-0.5, 0.5)
        noise = -scale * (1 if u >= 0 else -1) * math.log(1 - 2*abs(u))
        noisy = value + noise
        return max(self.config.amount_min, min(noisy, self.config.amount_max))

    def get_privacy_report(self) -> Dict[str, Any]:
        return {
            "total_budget": self.max_epsilon,
            "spent": self.spent_epsilon,
            "remaining": self.remaining_budget(),
            "by_category": dict(self.epsilon_by_category),
            "queries": len(self.query_log)
        }
