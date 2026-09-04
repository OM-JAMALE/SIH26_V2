import uuid
from typing import Union


def parse_uuid(val: Union[str, uuid.UUID]) -> uuid.UUID:
    """Safely parse a string or UUID object into a valid UUID.
    
    If val is already a UUID object, returns it.
    If val is a valid hex string, returns UUID(val).
    Otherwise generates a deterministic UUID v5 from string.
    """
    if isinstance(val, uuid.UUID):
        return val
    if not val:
        return uuid.uuid4()
    try:
        return uuid.UUID(str(val))
    except Exception:
        return uuid.uuid5(uuid.NAMESPACE_DNS, str(val))
