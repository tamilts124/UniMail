"""
modules/tempmailq.py - client for tempmailq.com  (used by main.py)

CSRF PROTOCOL — confirmed from HAR 2026-06-27:
  Laravel uses TWO separate CSRF mechanisms simultaneously:

  1. x-xsrf-token HEADER  — the XSRF-TOKEN cookie value (base64 encrypted,
     rotates on every response). Read from cookie jar after every call.

  2. _token BODY FIELD — a plain 40-char alphanumeric token scraped from
     <meta name="csrf-token" content="..."> in the homepage HTML.
     This is CONSTANT for the lifetime of the laravel_session cookie.
     It is COMPLETELY DIFFERENT from the XSRF-TOKEN cookie value.

  Both must be sent on every POST.
"""

import random
import string
import json
import os
import re
import urllib.parse
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

SESSION_FILE = os.path.join(os.path.dirname(__file__), '..', 'session.json')
BASE_URL     = "https://tempmailq.com"
IMPERSONATE  = "chrome124"
HTTP_TIMEOUT = 20
DOMAINS      = ["wqacmjaqe.xyz"]


# ── low-level helpers ──────────────────────────────────────────────────────

def _new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        'Accept':          'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer':         BASE_URL + '/',
        'Origin':          BASE_URL,
    })
    return s


def _xsrf(s: curl_requests.Session) -> str:
    """Return decoded XSRF-TOKEN cookie (goes as x-xsrf-token header)."""
    raw = s.cookies.get('XSRF-TOKEN')
    return urllib.parse.unquote(raw) if raw else ''


def _extract_meta_token(html_text: str) -> str:
    """Scrape the 40-char _token from <meta name="csrf-token" content="...">."""
    m = re.search(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([A-Za-z0-9+/=]{20,})["\']',
                  html_text)
    if m:
        return m.group(1)
    m2 = re.search(r'["\']csrfToken["\']\s*:\s*["\']([A-Za-z0-9+/=]{20,})["\']', html_text)
    if m2:
        return m2.group(1)
    return ''


def _seed(s: curl_requests.Session) -> tuple[str, str]:
    """GET homepage. Returns (xsrf_cookie_value, meta_csrf_token)."""
    resp = s.get(BASE_URL + '/', timeout=HTTP_TIMEOUT)
    return _xsrf(s), _extract_meta_token(resp.text)


def _post(s: curl_requests.Session, endpoint: str, data: dict,
          xsrf: str, meta_token: str) -> tuple[dict, str, str]:
    """
    POST with x-xsrf-token header + _token body field.
    On 419: re-seeds and retries once.
    Returns (body, new_xsrf, meta_token).
    """
    payload = dict(data)
    payload['_token'] = meta_token
    headers = {'x-xsrf-token': xsrf} if xsrf else {}
    resp = s.post(BASE_URL + endpoint, json=payload, headers=headers, timeout=HTTP_TIMEOUT)
    if resp.status_code == 419:
        xsrf, meta_token = _seed(s)
        payload['_token'] = meta_token
        headers = {'x-xsrf-token': xsrf}
        resp = s.post(BASE_URL + endpoint, json=payload, headers=headers, timeout=HTTP_TIMEOUT)
    xsrf = _xsrf(s) or xsrf
    try:
        body = resp.json()
    except Exception:
        body = {'error': f'HTTP {resp.status_code}: {resp.text[:300]}'}
    return body, xsrf, meta_token


# ── TempMailQ class ────────────────────────────────────────────────────────

class TempMailQ:
    """
    Single-mailbox client for tempmailq.com.

    Initialization order:
      1. Try to restore from session.json.
         - Validate with /get_messages.
         - If session is alive but on wrong address: /change to correct it.
      2. If restore fails: fresh GET / + /change to establish address.
    """

    def __init__(self, email: str | None = None):
        self.session       = _new_session()
        self.xsrf_token    = ''
        self.meta_token    = ''   # the _token scraped from page HTML
        self.current_email = email
        self.email_token   = ''

        if not self._restore():
            self._init(email)

    # ── persistence ────────────────────────────────────────────────────────

    def _save(self):
        data = {
            'cookies':       dict(self.session.cookies),
            'xsrf_token':    self.xsrf_token,
            'meta_token':    self.meta_token,
            'current_email': self.current_email,
            'email_token':   self.email_token,
        }
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def _restore(self) -> bool:
        if not os.path.exists(SESSION_FILE):
            return False
        try:
            with open(SESSION_FILE) as f:
                data = json.load(f)
        except Exception:
            return False

        saved_cookies    = data.get('cookies', {})
        saved_xsrf       = data.get('xsrf_token', '')
        saved_meta_token = data.get('meta_token', '')
        saved_email      = data.get('current_email', '')
        saved_etoken     = data.get('email_token', '')

        if not saved_cookies or not saved_xsrf or not saved_meta_token:
            return False

        for k, v in saved_cookies.items():
            self.session.cookies.set(k, v, domain='tempmailq.com')

        body, xsrf, meta = _post(self.session, '/get_messages', {},
                                 saved_xsrf, saved_meta_token)
        if 'error' in body:
            return False

        self.xsrf_token  = xsrf
        self.meta_token  = meta
        self.email_token = body.get('email_token', saved_etoken)
        active           = body.get('mailbox', '')
        desired          = self.current_email or saved_email

        if active == desired or not desired:
            self.current_email = active or desired
            self._save()
            return True

        # Switch to desired address
        user, domain = desired.split('@', 1)
        body2, xsrf2, meta2 = _post(self.session, '/change',
                                    {'name': user, 'domain': domain}, xsrf, meta)
        self.xsrf_token  = xsrf2
        self.meta_token  = meta2
        if 'error' not in body2 and body2.get('mailbox'):
            self.current_email = body2['mailbox']
            self.email_token   = body2.get('email_token', self.email_token)
        else:
            self.current_email = active  # accept whatever server has
        self._save()
        return True

    def _init(self, email: str | None):
        """Fresh session: GET / to get both tokens, then /change to get address."""
        self.xsrf_token, self.meta_token = _seed(self.session)
        if not self.meta_token:
            raise RuntimeError("tempmailq: could not extract csrf meta token from homepage HTML")
        if email:
            user, domain = email.split('@', 1)
        else:
            user   = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            domain = DOMAINS[0]
        body, xsrf, meta = _post(self.session, '/change',
                                 {'name': user, 'domain': domain},
                                 self.xsrf_token, self.meta_token)
        if 'error' in body or not body.get('mailbox'):
            raise RuntimeError(f"tempmailq: /change failed: {body}")
        self.xsrf_token    = xsrf
        self.meta_token    = meta
        self.current_email = body['mailbox']
        self.email_token   = body.get('email_token', '')
        self._save()

    # ── internal call helper ───────────────────────────────────────────────

    def _call(self, endpoint: str, data: dict | None = None) -> dict:
        body, xsrf, meta = _post(self.session, endpoint, data or {},
                                 self.xsrf_token, self.meta_token)
        self.xsrf_token = xsrf
        self.meta_token = meta
        if 'mailbox' in body:
            self.current_email = body['mailbox']
        if 'email_token' in body:
            self.email_token = body['email_token']
        self._save()
        return body

    # ── public API ─────────────────────────────────────────────────────────

    def get_current_email(self) -> str:
        return self.current_email or ''

    def refresh_emails(self) -> list[dict]:
        """Poll /get_messages. Returns list of {id, sender, subject, time, body, links}."""
        data = self._call('/get_messages')
        if 'error' in data:
            return []
        parsed = []
        for m in data.get('messages', []):
            body_html = m.get('body', '') or m.get('content', '') or ''
            soup      = BeautifulSoup(body_html, 'html.parser')
            body_text = soup.get_text(separator='\n').strip()
            links     = [a['href'] for a in soup.find_all('a', href=True)]
            parsed.append({
                'id':      m.get('id'),
                'sender':  m.get('from') or m.get('from_email', ''),
                'subject': m.get('subject', '(no subject)'),
                'time':    m.get('receivedAt') or m.get('created_at', ''),
                'body':    body_text or '(empty)',
                'links':   links,
            })
        return parsed

    def list_history(self) -> list[str]:
        """Return email addresses from session history."""
        data = self._call('/get_messages')
        if 'error' in data:
            return []
        return [h['email'] for h in data.get('histories', [])]

    def create_email(self, alias: str | None = None, domain: str | None = None) -> str | None:
        """Switch to a different address via /change."""
        if not alias:
            alias = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        if not domain:
            domain = DOMAINS[0]
        data = self._call('/change', {'name': alias, 'domain': domain})
        return None if 'error' in data else self.current_email

    def delete_email(self) -> str | None:
        """Delete current address via /delete."""
        data = self._call('/delete')
        return None if 'error' in data else self.current_email
