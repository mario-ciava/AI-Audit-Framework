import math
from collections import deque
from typing import Any, Dict, List, Optional
from .config import Config

class MultivariateDriftDetector:
    """Lightweight multivariate drift detection using diagonal Hotelling's T^2."""
    def __init__(self, config: Config):
        self.config = config
        self.window_size = config.drift_window_size
        self.threshold = config.drift_threshold
        self.mode = config.drift_mode
        self.reference_window = deque(maxlen=self.window_size)
        self.test_window = deque(maxlen=self.window_size)
        self.n_features: Optional[int] = None
        self.drift_scores: List[float] = []

    def update(self, observation: List[float]) -> Dict[str, Any]:
        if self.n_features is None:
            self.n_features = len(observation)
        elif len(observation) != self.n_features:
            raise ValueError(f"Expected {self.n_features} features")

        if len(self.reference_window) < self.window_size:
            self.reference_window.append(observation)
            return {"drift": False, "score": 0.0, "filling_reference": True}

        self.test_window.append(observation)
        if len(self.test_window) < max(1, self.config.min_test_samples):
            return {"drift": False, "score": 0.0, "filling_test": True}

        ref = list(self.reference_window)
        test = list(self.test_window)

        mean_ref = [sum(r[i] for r in ref)/len(ref) for i in range(self.n_features)]
        mean_test = [sum(t[i] for t in test)/len(test) for i in range(self.n_features)]

        t2 = 0.0
        for i in range(self.n_features):
            vals = [r[i] for r in ref]
            mean_i = mean_ref[i]
            var_ref = sum((v - mean_i)**2 for v in vals) / max(len(vals)-1, 1)
            if var_ref > 0:
                t2 += (mean_test[i] - mean_ref[i])**2 / var_ref

        score = math.sqrt(t2 / max(self.n_features, 1))
        self.drift_scores.append(score)
        is_drift = score > self.threshold

        if is_drift and len(self.test_window) >= self.window_size:
            from collections import deque
            self.reference_window = deque(list(self.test_window), maxlen=self.window_size)
            self.test_window.clear()

        return {
            "drift": is_drift, "score": score, "threshold": self.threshold, "mode": self.mode,
            "n_obs_ref": len(self.reference_window), "n_obs_test": len(self.test_window)
        }
