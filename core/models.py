from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class Decision:
    decision: str
    confidence: float

@dataclass
class Context:
    values: Dict[str, Any]
    features: Optional[List[float]] = None

@dataclass
class AuditResult:
    audit_id: str
    block_hash: str
    constraints: Dict[str, Any]
    drift: Optional[Dict[str, Any]]
    privacy_budget: Dict[str, Any]
    decision: Dict[str, Any]
