import csv
from pathlib import Path
from typing import Dict

from core.config import Config
from core.orchestrator import AuditOrchestrator

def main():
    print("="*70)
    print("AI AUDIT FRAMEWORK - TOY MORTGAGE EDITION")
    print("="*70)

    config = Config(max_epsilon=20.0, drift_threshold=2.5, drift_window_size=50, schema_version="1.0.0")
    orchestrator = AuditOrchestrator(config)

    print("\n[1] CLEAN RETAIL MORTGAGE REQUEST")
    print("-"*40)
    decision1 = {"decision":"APPROVE","confidence":0.85}
    context1 = {
        "loan_amount":150000,
        "property_value":200000,
        "monthly_debt":1000,
        "monthly_income":6000,
        "marginal_var":0.5,
        "var_limit":1.0,
        "features":[150000,200000,1000,6000,0.5]
    }
    result1 = orchestrator.audit_decision(decision1, context1)
    print(f"✓ Loan ID: {result1['audit_id']}")
    print(f"✓ Underwriting checks passed: {result1['constraints']['passed']}")
    print(f"✓ Block hash: {result1['block_hash'][:16]}...")
    print(f"✓ Privacy budget spent: {result1['privacy_budget']['spent']:.2f}")

    print("\n[2] STRESSED BORROWER (POLICY FAIL)")
    print("-"*40)
    decision2 = {"decision":"APPROVE","confidence":0.90}
    context2 = {
        "loan_amount":200000,
        "property_value":210000,
        "monthly_debt":3000,
        "monthly_income":5000,
        "marginal_var":1.5,
        "var_limit":1.0,
        "features":[200000,210000,3000,5000,1.5]
    }
    result2 = orchestrator.audit_decision(decision2, context2)
    print(f"✗ Violations found: {len(result2['constraints']['violations'])} (LTV/DSR/VAR)")
    for v in result2['constraints']['violations']:
        print(f"  - {v['id']}: {v['description']}")

    print("\n[3] PORTFOLIO DRIFT CHECK")
    print("-"*40)
    drift_notified = False
    for i in range(25):
        decision = {"decision":"APPROVE","confidence":0.8}
        context = {"loan_amount":150000+i*100,"property_value":200000,"monthly_debt":1000,"monthly_income":6000,"marginal_var":0.5,"var_limit":1.0,"features":[150000+i*100,200000,1000,6000,0.5]}
        orchestrator.audit_decision(decision, context)
    for i in range(25):
        decision = {"decision":"APPROVE","confidence":0.6}
        context = {"loan_amount":300000+i*500,"property_value":350000,"monthly_debt":4000,"monthly_income":8000,"marginal_var":0.9,"var_limit":1.0,"features":[300000+i*500,350000,4000,8000,0.9]}
        result = orchestrator.audit_decision(decision, context)
        if result["drift"] and result["drift"].get("drift"):
            print(f"⚠ Drift detected after {orchestrator.decisions_count} mortgage decisions")
            print(f"  Score: {result['drift']['score']:.2f} > threshold: {result['drift']['threshold']}")
            print(f"  Mode: {result['drift']['mode']} (diagonal covariance)")
            drift_notified = True
            break
    if not drift_notified:
        print("No drift detected within the stress window.")

    print("\n[4] SYSTEMATIC TESTING (POLICY/SECURITY)")
    print("-"*40)
    test_results = orchestrator.run_system_tests()
    print(f"Total tests: {test_results['total_tests']}")
    print(f"Passed: {test_results['passed']} ✓")
    print(f"Failed: {test_results['failed']}")
    print("\nTest Coverage by Category:")
    for category, stats in test_results["by_category"].items():
        status = "✓" if stats['passed'] == stats['total'] else "✗"
        print(f"  {category}: {stats['passed']}/{stats['total']} {status}")
    if test_results["failures"]:
        print("\nFailed tests:")
        for failure in test_results["failures"]:
            print(f"  ✗ {failure['id']}: expected '{failure['expected_behavior']}', got '{failure['actual_result']}'")

    print("\n[5] INTEGRITY VERIFICATION")
    print("-"*40)
    integrity = orchestrator.verify_integrity()
    print(f"✓ Chain integrity: {'VALID' if integrity['chain_integrity'] else 'INVALID'}")
    print(f"✓ Chain length: {integrity['chain_length']} blocks")
    print(f"✓ Total decisions audited: {integrity['total_decisions']}")
    print(f"✓ Drift detections: {integrity['total_drift_detections']}")

    privacy = integrity['privacy_budget']
    print("\nPrivacy Budget Report:")
    print(f"  Total budget: {privacy['total_budget']}ε")
    print(f"  Spent: {privacy['spent']:.2f}ε ({privacy['spent']/privacy['total_budget']*100:.1f}%)")
    print(f"  Remaining: {privacy['remaining']:.2f}ε")
    if privacy.get('by_category'):
        print("  Spending by category:")
        for cat, eps in privacy['by_category'].items():
            print(f"    - {cat}: {eps:.3f}ε")

    print("\nSystem Configuration:")
    print(f"  Schema version: {integrity['config']['schema_version']}")
    print(f"  Component version: {integrity['config']['component_version']}")
    print(f"  Drift detection mode: {integrity['config']['drift_mode']}")

    if integrity['chain_errors']:
        print("\n✗ Chain errors found:")
        for err in integrity['chain_errors']:
            print(f"  - {err}")

    print("\n"+"="*70)
    print("MORTGAGE DEMO COMPLETE - Nothing blockchainy, just hashes")
    print("Note: HMAC provides integrity/authenticity but NOT non-repudiation")
    print("="*70)

def run_batch_from_csv(data_path: str = "data/sample_mortgages.csv", *, silent: bool = False) -> Dict[str, int]:
    """
    Replay a batch of toy mortgage decisions sourced from CSV.
    The file ships with fake-but-plausible numeric ranges.
    """
    path = Path(data_path)
    if not path.exists():
        if not silent:
            print(f"Dataset '{data_path}' not found.")
        return {"processed": 0, "violations": 0}

    config = Config(max_epsilon=20.0, drift_threshold=2.5, drift_window_size=50, schema_version="1.0.0")
    orchestrator = AuditOrchestrator(config)
    processed = 0
    violations = 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                decision = _row_to_decision(row)
                context = _row_to_context(row)
            except ValueError as exc:
                if not silent:
                    print(f"Skipping row {row.get('id','?')}: {exc}")
                continue
            result = orchestrator.audit_decision(decision, context)
            processed += 1
            violations += len(result["constraints"]["violations"])

    if not silent:
        print(f"Processed {processed} mortgage rows from {data_path}")
        print(f"Policy violations recorded: {violations}")
        integrity = orchestrator.verify_integrity()
        print(f"Chain length now {integrity['chain_length']} blocks (valid={integrity['chain_integrity']})")
    return {"processed": processed, "violations": violations}

def _row_to_decision(row: Dict[str, str]) -> Dict[str, str]:
    confidence = float(row.get("confidence", 0.0) or 0.0)
    return {
        "decision": row.get("decision", "REVIEW"),
        "confidence": max(0.0, min(confidence, 1.0))
    }

def _row_to_context(row: Dict[str, str]) -> Dict[str, float]:
    def _f(key: str, default: float) -> float:
        raw = row.get(key, "")
        return float(raw) if str(raw).strip() else default

    context = {
        "loan_amount": _f("loan_amount", 0.0),
        "property_value": _f("property_value", 1.0),
        "monthly_debt": _f("monthly_debt", 0.0),
        "monthly_income": _f("monthly_income", 1.0),
        "marginal_var": _f("marginal_var", 0.0),
        "var_limit": _f("var_limit", 1.0),
    }
    context["features"] = [
        context["loan_amount"],
        context["property_value"],
        context["monthly_debt"],
        context["monthly_income"],
        context["marginal_var"]
    ]
    return context

if __name__ == "__main__":
    main()
