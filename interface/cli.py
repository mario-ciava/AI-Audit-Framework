import argparse, json
from core.config import Config
from core.orchestrator import AuditOrchestrator
from .demo import main as demo_main

def main():
    p = argparse.ArgumentParser(description="AI Audit Framework CLI (minimal)")
    p.add_argument("--verify", action="store_true", help="Verify Merkle chain integrity")
    p.add_argument("--tests", action="store_true", help="Run deterministic test suite")
    p.add_argument("--demo", action="store_true", help="Run the demo sequence")
    args = p.parse_args()

    orch = AuditOrchestrator(Config(max_epsilon=20.0, drift_threshold=2.5, drift_window_size=50))

    if args.tests:
        print(json.dumps(orch.run_system_tests(), indent=2)); return
    if args.verify:
        print(json.dumps(orch.verify_integrity(), indent=2)); return

    demo_main()

if __name__ == "__main__":
    main()
