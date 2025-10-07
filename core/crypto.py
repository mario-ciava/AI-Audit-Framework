import hashlib
import hmac
import secrets

class SimpleCrypto:
    """
    Real cryptography using HMAC-SHA256.
    In production, use nacl.signing or cryptography library.
    """
    def __init__(self):
        self.key = secrets.token_bytes(32)

    def sign(self, message: bytes) -> bytes:
        return hmac.new(self.key, message, hashlib.sha256).digest()

    def verify(self, message: bytes, signature: bytes) -> bool:
        expected = self.sign(message)
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
