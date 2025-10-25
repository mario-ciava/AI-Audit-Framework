import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence

class ConstraintChecker:
    @dataclass
    class Constraint:
        id: str
        check_fn: Callable[[Dict[str, Any]], bool]
        severity: str
        description: str

    def __init__(self):
        self.constraints: Dict[str, ConstraintChecker.Constraint] = {}

    def add_constraint(self, constraint: 'ConstraintChecker.Constraint'):
        self.constraints[constraint.id] = constraint

    def check(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        violations = []
        for c in self.constraints.values():
            try:
                if not c.check_fn(context):
                    violations.append({"id": c.id, "severity": c.severity, "description": c.description})
            except (KeyError, TypeError, ZeroDivisionError) as e:
                violations.append({"id": c.id, "severity": "error", "description": f"Check failed: {e}"})
        return violations

def build_constraints_from_specs(specs: Sequence[Dict[str, Any]]) -> ConstraintChecker:
    checker = ConstraintChecker()
    for spec in specs:
        check_fn = _constraint_fn_from_spec(spec)
        checker.add_constraint(ConstraintChecker.Constraint(
            id=spec["id"],
            severity=spec.get("severity","info"),
            description=spec.get("description",""),
            check_fn=check_fn
        ))
    return checker

def _constraint_fn_from_spec(spec: Dict[str, Any]) -> Callable[[Dict[str, Any]], bool]:
    ctype = spec.get("type")
    if ctype == "ratio_max":
        numerator = spec["numerator"]
        denominator = spec["denominator"]
        limit = float(spec["max"])
        min_denominator = float(spec.get("min_denominator", 1.0))
        def check_fn(ctx: Dict[str, Any]) -> bool:
            denom = max(float(ctx.get(denominator, 0.0)), min_denominator)
            num = float(ctx.get(numerator, 0.0))
            return (num / denom) <= limit
        return check_fn
    if ctype == "lte_field":
        field = spec["field"]
        other = spec["other_field"]
        fallback = float(spec.get("other_default", float("inf")))
        def check_fn(ctx: Dict[str, Any]) -> bool:
            lhs = float(ctx.get(field, 0.0))
            rhs = float(ctx.get(other, fallback))
            return lhs <= rhs
        return check_fn
    if ctype == "positive":
        fields = list(spec.get("fields", []))
        def check_fn(ctx: Dict[str, Any]) -> bool:
            return all(float(ctx.get(f, 0.0)) > 0 for f in fields)
        return check_fn
    if ctype == "value_max":
        field = spec["field"]
        limit = float(spec["max"])
        def check_fn(ctx: Dict[str, Any]) -> bool:
            return float(ctx.get(field, 0.0)) <= limit
        return check_fn
    if ctype == "value_min":
        field = spec["field"]
        limit = float(spec["min"])
        def check_fn(ctx: Dict[str, Any]) -> bool:
            return float(ctx.get(field, 0.0)) >= limit
        return check_fn
    raise ValueError(f"Unsupported constraint type: {ctype}")

def load_constraints_from_json(path: str) -> ConstraintChecker:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        specs = payload.get("constraints", [])
    else:
        specs = payload
    if not isinstance(specs, list):
        raise ValueError("Constraint definition must be a list or wrap a 'constraints' key")
    return build_constraints_from_specs(specs)

DEFAULT_FINANCIAL_CONSTRAINTS: List[Dict[str, Any]] = [
    {
        "id": "ltv_limit",
        "type": "ratio_max",
        "numerator": "loan_amount",
        "denominator": "property_value",
        "max": 0.8,
        "severity": "high",
        "description": "Loan-to-value ratio must be <= 80%"
    },
    {
        "id": "dsr_limit",
        "type": "ratio_max",
        "numerator": "monthly_debt",
        "denominator": "monthly_income",
        "max": 0.35,
        "severity": "high",
        "description": "Debt service ratio must be <= 35%"
    },
    {
        "id": "var_limit",
        "type": "lte_field",
        "field": "marginal_var",
        "other_field": "var_limit",
        "other_default": 1.0,
        "severity": "critical",
        "description": "VaR must be within limit"
    },
    {
        "id": "positive_amounts",
        "type": "positive",
        "fields": ["loan_amount","property_value","monthly_income"],
        "severity": "critical",
        "description": "All amounts must be positive"
    }
]

def setup_financial_constraints() -> ConstraintChecker:
    return build_constraints_from_specs(DEFAULT_FINANCIAL_CONSTRAINTS)

STRICT_FINANCIAL_CONSTRAINTS: List[Dict[str, Any]] = [
    {
        "id": "ltv_limit_strict",
        "type": "ratio_max",
        "numerator": "loan_amount",
        "denominator": "property_value",
        "max": 0.7,
        "severity": "critical",
        "description": "Strict LTV: <= 70%"
    },
    {
        "id": "dsr_limit_strict",
        "type": "ratio_max",
        "numerator": "monthly_debt",
        "denominator": "monthly_income",
        "max": 0.3,
        "severity": "critical",
        "description": "Strict DSR: <= 30%"
    },
    {
        "id": "var_limit_strict",
        "type": "lte_field",
        "field": "marginal_var",
        "other_field": "var_limit",
        "other_default": 0.9,
        "severity": "critical",
        "description": "Strict VaR limit"
    },
    {
        "id": "min_income",
        "type": "value_min",
        "field": "monthly_income",
        "min": 2500,
        "severity": "high",
        "description": "Borrower must earn >= 2.5k per month"
    },
    {
        "id": "positive_amounts",
        "type": "positive",
        "fields": ["loan_amount","property_value","monthly_income"],
        "severity": "critical",
        "description": "All amounts must be positive"
    }
]

def setup_financial_strict_constraints() -> ConstraintChecker:
    return build_constraints_from_specs(STRICT_FINANCIAL_CONSTRAINTS)

POLICY_REGISTRY: Dict[str, Callable[[], ConstraintChecker]] = {}

def register_policy_profile(name: str, builder: Callable[[], ConstraintChecker]):
    POLICY_REGISTRY[name] = builder

def get_policy_profile(name: str) -> ConstraintChecker:
    if name not in POLICY_REGISTRY:
        raise ValueError(f"Unknown policy profile '{name}'")
    return POLICY_REGISTRY[name]()

register_policy_profile("financial_basic", setup_financial_constraints)
register_policy_profile("financial_strict", setup_financial_strict_constraints)
