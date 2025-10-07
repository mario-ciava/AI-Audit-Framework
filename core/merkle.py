import threading, time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from .crypto import SimpleCrypto
from .utils import canonical_json

@dataclass
class MerkleNode:
    index: int
    timestamp: float
    data: Dict[str, Any]
    prev_hash: str
    hash: str
    signature: bytes

class MerkleChain:
    """Tamper-evident log via hash chaining and HMAC signatures."""
    def __init__(self, crypto: SimpleCrypto):
        self.crypto = crypto
        self.chain: List[MerkleNode] = []
        self._lock = threading.RLock()
        self._create_genesis()

    def _create_genesis(self):
        data = {"type": "genesis", "timestamp": time.time()}
        with self._lock:
            self._add_block(data, prev_hash="0"*64)

    def _compute_hash(self, index: int, timestamp: float, data: Dict, prev_hash: str) -> str:
        block_content = {"index": index, "timestamp": timestamp, "data": data, "prev_hash": prev_hash}
        return self.crypto.hash(canonical_json(block_content).encode())

    def _add_block(self, data: Dict[str, Any], prev_hash: str) -> str:
        index = len(self.chain)
        timestamp = time.time()
        block_hash = self._compute_hash(index, timestamp, data, prev_hash)
        signature = self.crypto.sign(block_hash.encode())
        node = MerkleNode(index, timestamp, data, prev_hash, block_hash, signature)
        self.chain.append(node)
        return block_hash

    def add_record(self, data: Dict[str, Any]) -> str:
        with self._lock:
            prev_hash = self.chain[-1].hash if self.chain else "0"*64
            return self._add_block(data, prev_hash)

    def verify_integrity(self) -> Tuple[bool, List[str]]:
        errors = []
        with self._lock:
            for i, node in enumerate(self.chain):
                expected_hash = self._compute_hash(node.index, node.timestamp, node.data, node.prev_hash)
                if node.hash != expected_hash:
                    errors.append(f"Block {i}: hash mismatch")
                if not self.crypto.verify(node.hash.encode(), node.signature):
                    errors.append(f"Block {i}: invalid signature")
                if i > 0 and node.prev_hash != self.chain[i-1].hash:
                    errors.append(f"Block {i}: broken chain link")
        return len(errors) == 0, errors
