from dataclasses import dataclass
from typing import Any, Callable, Dict, List

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

def setup_financial_constraints() -> ConstraintChecker:
    checker = ConstraintChecker()
    checker.add_constraint(ConstraintChecker.Constraint(
        id="ltv_limit",
        check_fn=lambda ctx: (ctx.get("loan_amount", 0) / max(ctx.get("property_value", 1), 1)) <= 0.8,
        severity="high",
        description="Loan-to-value ratio must be <= 80%"
    ))
    checker.add_constraint(ConstraintChecker.Constraint(
        id="dsr_limit",
        check_fn=lambda ctx: (ctx.get("monthly_debt", 0) / max(ctx.get("monthly_income", 1), 1)) <= 0.35,
        severity="high",
        description="Debt service ratio must be <= 35%"
    ))
    checker.add_constraint(ConstraintChecker.Constraint(
        id="var_limit",
        check_fn=lambda ctx: ctx.get("marginal_var", 0) <= ctx.get("var_limit", 1.0),
        severity="critical",
        description="VaR must be within limit"
    ))
    checker.add_constraint(ConstraintChecker.Constraint(
        id="positive_amounts",
        check_fn=lambda ctx: all(ctx.get(k, 0) > 0 for k in ["loan_amount","property_value","monthly_income"]),
        severity="critical",
        description="All amounts must be positive"
    ))
    return checker
