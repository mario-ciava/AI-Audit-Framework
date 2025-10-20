import hashlib
import hmac
import os
import secrets
from pathlib import Path
from typing import Optional

class SimpleCrypto:
    """
    Real cryptography using HMAC-SHA256.
    In production, use nacl.signing or cryptography library.
    """
    def __init__(self, key_path: Optional[str] = None):
        self.key_path = Path(key_path) if key_path else None
        self.key = self._load_or_create_key()

    def _load_or_create_key(self) -> bytes:
        if not self.key_path:
            return secrets.token_bytes(32)
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if self.key_path.exists():
            data = self.key_path.read_bytes()
            if len(data) != 32:
                raise ValueError("Stored HMAC key must be 32 bytes")
            return data
        key = secrets.token_bytes(32)
        with open(self.key_path, "wb") as fh:
            fh.write(key)
        try:
            os.chmod(self.key_path, 0o600)
        except PermissionError:
            pass
        return key

    def sign(self, message: bytes) -> bytes:
        return hmac.new(self.key, message, hashlib.sha256).digest()

    def verify(self, message: bytes, signature: bytes) -> bool:
        expected = self.sign(message)
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
