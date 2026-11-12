"""Clearance codes (like Bandit passwords): finish a ticket, get the code for the next one,
type `unlock CODE` on any computer to jump there. Codes are derived, so nothing has to be stored."""
import hashlib
import re

SALT = "horizon-linuxip-clearance-v1"
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def code_for(level):
    digest = hashlib.sha256(f"{SALT}:{level}".encode()).digest()
    body = "".join(ALPHABET[b % len(ALPHABET)] for b in digest[:8])
    return f"HZN-{level:02d}-{body[:4]}-{body[4:]}"


def level_from_code(text, total):
    """Return the level a code unlocks, or None if the code is not valid."""
    m = re.fullmatch(r"HZN-(\d{1,2})-[A-Z0-9]{4}-[A-Z0-9]{4}", text.strip().upper())
    if not m:
        return None
    level = int(m.group(1))
    return level if 1 <= level <= total and code_for(level) == text.strip().upper() else None
