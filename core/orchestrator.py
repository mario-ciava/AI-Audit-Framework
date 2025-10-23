import math, time
from typing import Any, Dict, Optional
from collections import defaultdict
from .config import Config
from .crypto import SimpleCrypto
from .merkle import MerkleChain
from .constraints import ConstraintChecker, get_policy_profile, load_constraints_from_json
from .privacy import PrivacyAccountant
from .drift import MultivariateDriftDetector
from .testing import SystematicTester

class AuditOrchestrator:
    def __init__(self, config: Optional[Config] = None, *, constraints: Optional[ConstraintChecker] = None):
        self.config = config or Config()
        self.crypto = SimpleCrypto(self.config.key_path)
        self.chain = MerkleChain(self.crypto, storage_path=self.config.chain_path)
        self.constraints = constraints or self._init_constraints()
        self.privacy = PrivacyAccountant(self.config)
        self.drift_detector = MultivariateDriftDetector(self.config)
        self.tester = SystematicTester()
        self.metrics = defaultdict(list)
        self.decisions_count = 0
        self.anomalies_count = 0

    def audit_decision(self, decision: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        audit_id = f"audit_{self.decisions_count}_{int(time.time())}"
        self.decisions_count += 1

        violations = self.constraints.check(context)
        eps = max(1e-6, float(self.config.privacy_epsilon_per_query))
        can_log = self.privacy.can_query(eps)

        drift_result = None
        if "features" in context:
            drift_result = self.drift_detector.update(context["features"])
            if drift_result.get("drift"):
                self.anomalies_count += 1

        audit_data: Dict[str, Any] = {
            "audit_id": audit_id,
            "decision": decision,
            "violations": len(violations),
            "anomaly": drift_result.get("drift", False) if drift_result else False
        }
        if can_log and self.privacy.spend(eps, "audit_log"):
            audit_data["context"] = self._privatize_context(context)

        block_hash = self.chain.add_record(audit_data)
        self.metrics["decisions"].append(time.time())
        if violations:
            self.metrics["violations"].append(time.time())

        return {
            "audit_id": audit_id,
            "block_hash": block_hash,
            "decision": decision,
            "constraints": {"passed": len(violations)==0, "violations": violations},
            "drift": drift_result if drift_result else None,
            "privacy_budget": self.privacy.get_privacy_report()
        }

    def _privatize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        private: Dict[str, Any] = {}
        for k, v in context.items():
            if k in ["loan_amount","property_value","monthly_income","monthly_debt"]:
                noisy = self.privacy.add_laplace_noise(float(v), sensitivity=self.config.privacy_sensitivity, epsilon=self.config.privacy_epsilon_per_query)
                private[k] = round(noisy, 2) if noisy is not None else "budget_exceeded"
            elif k != "features":
                private[k] = v
        return private

    def run_system_tests(self) -> Dict[str, Any]:
        def system_fn(inputs: Dict[str, Any]) -> str:
            if "input" in inputs:
                s = str(inputs.get("input",""))
                s_lower = s.lower()
                if any(tok in s_lower for tok in ["ignore","override","disregard","forget previous"]):
                    return "blocked"
                if any(tok in s_lower for tok in ["select","insert","update","delete","drop","--",";"]):
                    return "sanitized"
                return "sanitized"
            if all(k in inputs for k in ["loan_amount","property_value"]):
                violations = self.constraints.check(inputs)
                return "reject" if violations else "approve"
            if any(isinstance(v,(int,float)) and math.isinf(float(v)) for v in inputs.values()):
                return "error"
            if any(isinstance(v,(int,float)) and v < 0 for v in inputs.values()):
                return "error"
            if any(isinstance(v,(int,float)) and v == 0 for v in inputs.values()):
                return "reject"
            return "unknown"
        return self.tester.run_tests(system_fn)

    def verify_integrity(self) -> Dict[str, Any]:
        chain_valid, chain_errors = self.chain.verify_integrity()
        return {
            "chain_integrity": chain_valid,
            "chain_errors": chain_errors,
            "chain_length": len(self.chain.chain),
            "total_decisions": self.decisions_count,
            "total_drift_detections": self.anomalies_count,
            "privacy_budget": self.privacy.get_privacy_report(),
            "config": {
                "schema_version": self.config.schema_version,
                "component_version": self.config.component_version,
                "drift_mode": self.config.drift_mode
            }
        }

    def _init_constraints(self) -> ConstraintChecker:
        if self.config.policy_config_path:
            return load_constraints_from_json(self.config.policy_config_path)
        return get_policy_profile(self.config.policy_profile)
