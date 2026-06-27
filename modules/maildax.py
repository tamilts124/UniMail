"""
modules/maildax.py - self-contained client for maildax.cc

Independent implementation from modules/tempmailq.py on purpose - even
though maildax.cc also happens to use a Laravel XSRF-TOKEN cookie for
CSRF, this module does not import or share any code with the
tempmailq module.

Uses curl_cffi (browser TLS/JA3 impersonation) so Cloudflare doesn't
fingerprint-block the requests.

CSRF scheme:
    XSRF-TOKEN cookie (Laravel) -> URL-decoded -> sent as
    `x-xsrf-token` header on every POST. No _token body field needed
    for this site.
"""

import json
import re
import urllib.parse
from curl_cffi import requests as curl_requests

BASE_URL = "https://maildax.cc"
DOMAINS = ["maildax.space", "maildax.store", "maildax.online"]
IMPERSONATE = "chrome124"


class Maildax:
    def __init__(self):
        self.base_url = BASE_URL
        self.domains = DOMAINS
        self.session = curl_requests.Session(impersonate=IMPERSONATE)
        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": self.base_url + "/",
            "Origin": self.base_url,
        })
        self.xsrf_token = None
        self.current_email = None
        self.email_token = None

    # ── internals ──────────────────────────────────────────────────

    def _read_xsrf_cookie(self):
        raw = self.session.cookies.get("XSRF-TOKEN")
        if raw:
            self.xsrf_token = urllib.parse.unquote(raw)

    def fetch_csrf(self):
        """GET homepage to seed cookies, then pull XSRF-TOKEN."""
        self.session.get(self.base_url + "/")
        self._read_xsrf_cookie()
        return self.xsrf_token

    def _post(self, endpoint, data):
        if not self.xsrf_token:
            self.fetch_csrf()
        headers = {"x-xsrf-token": self.xsrf_token} if self.xsrf_token else {}
        resp = self.session.post(self.base_url + endpoint, json=data, headers=headers)
        if resp.status_code == 419:
            self.fetch_csrf()
            headers = {"x-xsrf-token": self.xsrf_token} if self.xsrf_token else {}
            resp = self.session.post(self.base_url + endpoint, json=data, headers=headers)
        try:
            body = resp.json()
        except Exception:
            body = {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        self._read_xsrf_cookie()
        return body

    def _update(self, data):
        self.current_email = data.get("mailbox", self.current_email)
        self.email_token = data.get("email_token", self.email_token)

    # ── public API ─────────────────────────────────────────────────

    def list_domains(self):
        """Fetch live domain list from homepage, falling back to defaults."""
        try:
            resp = self.session.get(self.base_url + "/")
            self._read_xsrf_cookie()
            body = resp.text
            found = re.findall(r'<option[^>]*value=["\']([a-z0-9.-]+\.[a-z]{2,})["\']', body)
            if not found:
                found = re.findall(r'@([a-z0-9-]+\.[a-z]{2,})', body)
            if found:
                self.domains = list(dict.fromkeys(found))
        except Exception:
            pass
        return self.domains

    def get_messages(self):
        data = self._post("/get_messages", {})
        if "error" in data:
            return None
        self._update(data)
        return data

    def create_email(self, alias, domain):
        data = self._post("/change", {"name": alias, "domain": domain})
        if "error" in data:
            return None
        self._update(data)
        return self.current_email

    def delete_email(self):
        data = self._post("/delete", {})
        if "error" in data:
            return None
        self._update(data)
        return self.current_email
