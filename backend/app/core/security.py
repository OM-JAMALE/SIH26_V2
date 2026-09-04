from hashlib import sha256


def hash_identifier(identifier: str) -> str:
    """Create a non-reversible identifier for logs and correlation records."""
    return sha256(identifier.encode("utf-8")).hexdigest()
