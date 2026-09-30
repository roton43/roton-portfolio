import base64
import hashlib
import hmac
import os
import secrets
import time
from collections import OrderedDict


def hash_password(password):
    salt = secrets.token_bytes(16)
    rounds = 600000
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, rounds)
    return f'pbkdf2_sha256${rounds}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}'


def verify_password(password, stored):
    try:
        name, rounds, salt, digest = stored.split('$')
        if name != 'pbkdf2_sha256' or not 100000 <= int(rounds) <= 2000000:
            return False
        candidate = hashlib.pbkdf2_hmac('sha256', password.encode(), base64.b64decode(salt), int(rounds))
        return hmac.compare_digest(candidate, base64.b64decode(digest))
    except (ValueError, TypeError):
        return False


def admin_fingerprint():
    # Changing the password hash invalidates all existing sessions.
    return hashlib.sha256(os.getenv('ADMIN_PASSWORD_HASH', '').encode()).hexdigest()


def authenticated(request):
    return (request.session.get('admin') == admin_fingerprint()
            and request.session.get('expires', 0) > time.time())


def csrf_token(request):
    if not request.session.get('csrf'):
        request.session['csrf'] = secrets.token_urlsafe(32)
    return request.session['csrf']


def check_csrf(request, token):
    from fastapi import HTTPException
    expected = request.session.get('csrf', '')
    if not expected or not hmac.compare_digest(str(token), expected):
        raise HTTPException(403, 'The form expired. Reload the page and try again.')


class LoginLimiter:
    """Bounded, single-worker login limiter. Never trusts arbitrary forwarded headers."""
    def __init__(self):
        self.entries = OrderedDict()

    def allow(self, key):
        now = time.monotonic()
        for k in [k for k, v in self.entries.items() if now - v[0] > 900]:
            self.entries.pop(k, None)
        if key in self.entries and self.entries[key][1] >= 5:
            return False
        if key not in self.entries:
            if len(self.entries) >= 10000:
                self.entries.popitem(last=False)
            self.entries[key] = (now, 0)
        started, count = self.entries[key]
        self.entries[key] = (started, count + 1)
        return True

    def clear(self, key):
        self.entries.pop(key, None)
