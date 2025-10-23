# AI Audit Framework

> The project implements a compact, fully working core for **auditing AI or rule-based decisions** in financial workflows.  It focuses on correctness, determinism and clarity rather than feature count:

- **deterministic Merkle log** with HMAC-SHA256 for integrity and authenticity;
- **policy constraints** (LTV, DSR, VaR, positivity) evaluated safely — no `eval()`;  
- **privacy budget accounting** (ε-DP with Laplace noise and clipping);
- **lightweight multivariate drift detection** (Hotelling’s T², diagonal covariance);  
- **deterministic test suite** (boundary, policy, security categories).

It is a **prototype**, intentionally modest, meant for learning, validation and transparent experimentation. This **is not**:
- a production governance platform or compliance product;
- a blockchain, consensus or formal-verification system;
- a substitute for enterprise controls, secure key management or certified auditing solutions.

## Table of Contents

- [Architecture at a Glance](#architecture-at-a-glance)
- [Quick Start](#quick-start)
- [Library Usage](#library-usage)
- [Key Properties](#key-properties)
- [Security & Privacy Notes](#security--privacy-notes)
- [Limitations](#limitations)
- [How to Extend / Integrate](#how-to-extend--integrate)
- [Roadmap](#roadmap)

## Architecture at a Glance

| Stage | Component | Description |
|--------|------------|--------------|
| 1 | **Decision Input** | Model or rule decision with contextual data |
| 2 | **Constraint Checker** | Validates LTV, DSR, VaR and positivity constraints |
| 3 | **Drift Detector** | Detects distributional shifts using Hotelling’s T² (diagonal covariance) |
| 4 | **Privacy Accountant** | Tracks ε-DP budget, applies Laplace noise and value clipping |
| 5 | **Audit Record** | Aggregates decision data, constraint results and drift metrics |
| 6 | **Merkle Chain** | Appends HMAC-SHA256 hash-linked audit entries for tamper evidence |
| 7 | **Integrity Verification** | Checks full chain consistency and signature validity |
| 8 | **Deterministic Tests** | Runs reproducible QA for boundary, policy and security checks |

**Core modules**
- `config.py` — central parameters (privacy, drift, thresholds, versions);
- `crypto.py` — HMAC-SHA256 signing and hashing;
- `merkle.py` — hash-linked, signed audit records;  
- `constraints.py` — safe policy validation (pure functions);
- `privacy.py` — ε-DP budget management with Laplace noise and clipping;  
- `drift.py` — lightweight multivariate drift detection;
- `testing.py` — deterministic test suite;
- `orchestrator.py` — orchestration layer combining all components;
- `demo.py` / `cli.py` — runnable examples and minimal CLI interface which provides `--verify`, `--tests` and `--demo` commands.

## Quick Start

Requirements: **Python 3.10+**, no external dependencies.

1. Clone or copy the `ai_audit/` package into your workspace.  
2. From the project root, run the demo:
```bash
python3 -m interface.demo
```
You’ll see a complete report including:
- constraint checks (valid and invalid cases);
- drift simulation;
- deterministic test suite results;
- integrity verification;
- privacy budget usage.

By default the framework persists the Merkle chain and HMAC key under `audit_state/`, so repeated CLI runs can verify the exact same log. Remove that directory (or point `Config.chain_path` / `Config.key_path` elsewhere) to reset the history.

### Policy Profiles

Constraints are organized as profiles. The default `financial_basic` bundle mirrors the logic in `policies/financial_basic.json`. You can either select another registered profile via `Config(policy_profile="...")` or point `Config.policy_config_path` to a JSON file using the same schema:

```json
{
  "constraints": [
    {"id": "ltv_limit", "type": "ratio_max", "numerator": "...", "denominator": "...", "max": 0.8},
    {"id": "dsr_limit", "type": "ratio_max", ...},
    {"id": "var_limit", "type": "lte_field", "field": "marginal_var", "other_field": "var_limit"},
    {"id": "positive_amounts", "type": "positive", "fields": ["loan_amount", "..."]}
  ]
}
```

Supported constraint `type` values include:
- `ratio_max`: `numerator / denominator <= max` (with optional `min_denominator` safeguard);
- `lte_field`: left field must be less-or-equal than another field (with optional `other_default`);
- `positive`: every field listed must be strictly positive;
- `value_max`: single field must stay under a constant `max`.

## Library Usage

You can import and use the framework directly from the `ai_audit` package.  
Each component is modular, but the `AuditOrchestrator` provides a ready-to-use entry point that coordinates all parts (constraints, privacy, drift, Merkle logging and tests).

```python
from core.config import Config
from core.orchestrator import AuditOrchestrator

# Initialize configuration
config = Config(
    max_epsilon=20.0,         # Total privacy budget
    drift_threshold=2.5,      # Sensitivity for drift detection
    drift_window_size=50,     # Window size for drift reference/test
    schema_version="1.0.0"
)

# Create orchestrator instance
orch = AuditOrchestrator(config)

# Define decision and context
decision = {"decision": "APPROVE", "confidence": 0.85}
context = {
    "loan_amount": 150000,
    "property_value": 200000,
    "monthly_debt": 1000,
    "monthly_income": 6000,
    "marginal_var": 0.5,
    "var_limit": 1.0,
    "features": [150000, 200000, 1000, 6000, 0.5]
}

# Run audit
result = orch.audit_decision(decision, context)
print("\nAudit result:")
print(result)

# Verify Merkle chain integrity
print("\nIntegrity check:")
print(orch.verify_integrity())

# Run deterministic system tests
print("\nSystematic tests:")
print(orch.run_system_tests())
```

Alternatively, you can use the minimal CLI:

```bash
# Run deterministic test suite
python3 -m interface.cli --tests

# Verify Merkle chain integrity
python3 -m interface.cli --verify

# Run the demonstration sequence
python3 -m interface.cli --demo
```

## Key Properties

| Category       | Property                               | Purpose                                             |
|----------------|----------------------------------------|-----------------------------------------------------|
| Integrity      | Merkle chain + HMAC-SHA256             | Tamper-evidence and authenticity of audit records   |
| Privacy        | ε-DP budget + Laplace + clipping       | Controlled noise, bounded values, accountable spend |
| Policy         | Pure-function constraints              | Transparent pass/fail with human-readable reason    |
| Drift          | Hotelling’s T² (diagonal covariance)   | Sensitivity to statistical shifts                   |
| Testing        | Deterministic suite                    | Repeatable QA for boundary/policy/security cases    |
| Determinism    | Canonical JSON serialization           | Stable hashes and reproducible outputs              |
| Persistence    | Disk-backed Merkle chain + HMAC key    | Re-verifiable audit trail across sessions           |

## Security & Privacy Notes

- **HMAC-SHA256** ensures integrity and authenticity via a shared secret key. It does **not** ensure **non-repudiation** — use **Ed25519** or **ECDSA** for that.
- No networking, PoW or consensus is involved; the log is entirely local.  
- The privacy accountant tracks and enforces the total ε-budget; noisy outputs are clipped to configured bounds.  
- A re-entrant lock protects concurrent writes to the Merkle chain.
- The signing key and Merkle chain are stored locally (defaults under `audit_state/`). Protect or relocate these files via the configuration to fit your operational security requirements.

## Limitations

- Drift detection uses a **diagonal covariance** approximation; correlations between features are ignored. A full covariance variant would require NumPy, omitted intentionally for simplicity.
- Privacy accountant implements **basic ε-composition**; no advanced (e.g. Rényi) accounting methods.  
- No key management, storage, rotation or external attestation is included.  

## How to Extend / Integrate

- **Asymmetric signatures** — integrate Ed25519 for per-block non-repudiation.  
- **Full drift mode** — switch to full covariance or streaming estimators (NumPy).  
- **Configurable policies** — ship additional JSON profiles or build loaders from external systems.  
- **Persistence** — export the Merkle chain to disk or immutable storage (e.g., S3 Object Lock).  
- **Reporting** — produce JSON or HTML summaries for audit results and privacy usage.

## Roadmap

- [ ] Optional Ed25519 signatures for external attestation  
- [ ] NumPy-backed full-covariance drift mode  
- [x] Pluggable constraint registry (basic JSON policy profiles)   
- [ ] Simple HTML summary report (no web framework)
