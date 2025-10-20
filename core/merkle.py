import json
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
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
    def __init__(self, crypto: SimpleCrypto, storage_path: Optional[str] = None):
        self.crypto = crypto
        self.storage_path = Path(storage_path) if storage_path else None
        self.chain: List[MerkleNode] = []
        self._lock = threading.RLock()
        if not self._load_existing_chain():
            self._create_genesis()

    def _create_genesis(self):
        data = {"type": "genesis", "timestamp": time.time()}
        with self._lock:
            self._add_block(data, prev_hash="0"*64)

    def _load_existing_chain(self) -> bool:
        if not self.storage_path or not self.storage_path.exists():
            return False
        with self._lock:
            payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
            entries = payload.get("chain", [])
            if not entries:
                return False
            self.chain = [self._dict_to_node(entry) for entry in entries]
            valid, errors = self.verify_integrity()
            if not valid:
                raise ValueError(f"Stored Merkle chain failed integrity: {errors}")
            return True

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
        self._persist_locked()
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

    def _persist_locked(self):
        if not self.storage_path:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"chain": [self._node_to_dict(node) for node in self.chain]}
        tmp_path = self.storage_path.parent / (self.storage_path.name + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        os.replace(tmp_path, self.storage_path)

    @staticmethod
    def _node_to_dict(node: MerkleNode) -> Dict[str, Any]:
        return {
            "index": node.index,
            "timestamp": node.timestamp,
            "data": node.data,
            "prev_hash": node.prev_hash,
            "hash": node.hash,
            "signature": node.signature.hex()
        }

    @staticmethod
    def _dict_to_node(payload: Dict[str, Any]) -> MerkleNode:
        return MerkleNode(
            index=payload["index"],
            timestamp=payload["timestamp"],
            data=payload["data"],
            prev_hash=payload["prev_hash"],
            hash=payload["hash"],
            signature=bytes.fromhex(payload["signature"])
        )
