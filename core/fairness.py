from collections import defaultdict
from typing import Any, Dict, Iterable


def _extract_data(record: Any) -> Dict[str, Any]:
    if isinstance(record, dict):
        return record
    data = getattr(record, "data", None)
    if isinstance(data, dict):
        return data
    raise ValueError("Unsupported record format for fairness analysis")


def compute_group_metrics(records: Iterable[Any], attribute: str = "segment") -> Dict[str, Any]:
    by_group: Dict[str, Dict[str, float]] = {}
    members: Dict[str, int] = defaultdict(int)
    model_approvals: Dict[str, int] = defaultdict(int)
    final_approvals: Dict[str, int] = defaultdict(int)
    policy_blocks: Dict[str, int] = defaultdict(int)
    scores_sum: Dict[str, float] = defaultdict(float)

    for record in records:
        data = _extract_data(record)
        group = data.get(attribute) or (data.get("context", {}) if isinstance(data.get("context"), dict) else {}).get(attribute)
        if not group:
            continue
        members[group] += 1
        if data.get("model_decision") == "APPROVE":
            model_approvals[group] += 1
        if data.get("final_outcome") == "APPROVE":
            final_approvals[group] += 1
        if data.get("policy_blocked"):
            policy_blocks[group] += 1
        score = data.get("model_score")
        if isinstance(score, (int, float)):
            scores_sum[group] += float(score)

    metrics: Dict[str, Any] = {}
    for group, count in members.items():
        if count == 0:
            continue
        metrics[group] = {
            "count": count,
            "model_approval_rate": round(model_approvals[group] / count, 4),
            "final_approval_rate": round(final_approvals[group] / count, 4),
            "policy_override_rate": round(policy_blocks[group] / count, 4),
            "avg_model_score": round(scores_sum[group] / count, 4) if scores_sum[group] else 0.0,
        }

    if not metrics:
        return {"attribute": attribute, "groups": {}, "approval_span": 0.0}

    approval_rates = [data["final_approval_rate"] for data in metrics.values()]
    approval_span = round(max(approval_rates) - min(approval_rates), 4) if approval_rates else 0.0

    return {
        "attribute": attribute,
        "groups": metrics,
        "approval_span": approval_span
    }
