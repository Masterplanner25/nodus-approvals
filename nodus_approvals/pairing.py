"""PairingCode — generate and validate short numeric codes for peer access."""
from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta


def generate_code(length: int = 6) -> str:
    """Return a cryptographically random numeric code of *length* digits."""
    max_exclusive = 10 ** length
    code = secrets.randbelow(max_exclusive)
    return str(code).zfill(length)


@dataclass
class PairingEntry:
    """One pending or completed pairing request.

    Attributes
    ----------
    code:       The numeric code delivered to the requester.
    peer_id:    Identity of the peer requesting access.
    created_at: When the code was issued.
    expires_at: When the code expires.
    approved:   True after an operator calls ``approve()``.
    """

    code: str
    peer_id: str
    created_at: datetime
    expires_at: datetime
    approved: bool = False

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


class PairingStore:
    """Thread-safe in-memory store for pairing codes.

    Usage::

        store = PairingStore()
        code = store.issue("peer-123")          # returns e.g. "482910"
        # deliver code to operator via CLI
        entry = store.validate(code)            # returns PairingEntry
        store.approve(code)                     # marks as approved
    """

    def __init__(self) -> None:
        self._entries: dict[str, PairingEntry] = {}
        self._lock = threading.Lock()

    def issue(self, peer_id: str, ttl_seconds: int = 300) -> str:
        """Generate and store a new pairing code for *peer_id*.

        Returns the code string.  Any previous code for this peer is replaced.
        """
        code = generate_code()
        now = datetime.now(timezone.utc)
        entry = PairingEntry(
            code=code,
            peer_id=peer_id,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        with self._lock:
            # Remove any previous code for this peer
            old_codes = [k for k, v in self._entries.items() if v.peer_id == peer_id]
            for k in old_codes:
                del self._entries[k]
            self._entries[code] = entry
        return code

    def validate(self, code: str) -> PairingEntry | None:
        """Return the entry for *code* if it exists and has not expired."""
        with self._lock:
            entry = self._entries.get(code)
        if entry is None or entry.is_expired:
            return None
        return entry

    def approve(self, code: str) -> bool:
        """Mark the entry for *code* as approved. Returns True if found."""
        with self._lock:
            entry = self._entries.get(code)
            if entry is None or entry.is_expired:
                return False
            from dataclasses import replace
            self._entries[code] = replace(entry, approved=True)
        return True

    def is_approved(self, peer_id: str) -> bool:
        """Return True if any non-expired approved code exists for *peer_id*."""
        with self._lock:
            return any(
                e.peer_id == peer_id and e.approved and not e.is_expired
                for e in self._entries.values()
            )

    def expire_old(self) -> int:
        """Remove expired entries. Returns count removed."""
        with self._lock:
            expired = [k for k, v in self._entries.items() if v.is_expired]
            for k in expired:
                del self._entries[k]
        return len(expired)
