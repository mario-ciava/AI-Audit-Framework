import argparse, json
from core.config import Config
from core.orchestrator import AuditOrchestrator
from .demo import main as demo_main
from .demo import run_batch_from_csv

def main():
    p = argparse.ArgumentParser(description="AI Audit Framework CLI (minimal)")
    p.add_argument("--verify", action="store_true", help="Verify Merkle chain integrity")
    p.add_argument("--summary", action="store_true", help="Print a portfolio snapshot from the Merkle log")
    p.add_argument("--tests", action="store_true", help="Run deterministic test suite")
    p.add_argument("--demo", action="store_true", help="Run the demo sequence")
    p.add_argument("--demo-batch", action="store_true", help="Replay the mortgage CSV demo")
    p.add_argument("--data-path", default="data/sample_mortgages.csv", help="CSV dataset for --demo-batch")
    args = p.parse_args()

    config = Config(max_epsilon=20.0, drift_threshold=2.5, drift_window_size=50)

    if args.tests:
        orch = AuditOrchestrator(config)
        print(json.dumps(orch.run_system_tests(), indent=2))
        return
    if args.verify:
        orch = AuditOrchestrator(config)
        print(json.dumps(orch.verify_integrity(), indent=2))
        return
    if args.summary:
        orch = AuditOrchestrator(config)
        print(json.dumps(orch.get_portfolio_summary(), indent=2))
        return
    if args.demo_batch:
        run_batch_from_csv(args.data_path)
        return

    demo_main()

if __name__ == "__main__":
    main()
