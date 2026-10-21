#!/usr/bin/env python3
"""Utility to generate a Gmail OAuth 2.0 Refresh Token for HealthAware.

This script assists the project owner in obtaining a long-lived refresh token
with the `https://www.googleapis.com/auth/gmail.send` scope.

Prerequisites in Google Cloud Console (https://console.cloud.google.com/):
1. Create a Project (e.g. "HealthAware Production").
2. Enable the "Gmail API" (APIs & Services -> Enable APIs & Services -> search "Gmail API").
3. Configure OAuth Consent Screen:
   - User Type: External
   - App Name: HealthAware Email Relay
   - User Support Email: your email
   - Test Users: add your sending Gmail address (e.g. sreemani0323@gmail.com)
4. Create Credentials -> OAuth client ID:
   - Application type: Web application (or Desktop app)
   - Authorized redirect URIs:
     * http://localhost:8085/oauth2callback
     * https://developers.google.com/oauthplayground
   - Download or copy the Client ID and Client Secret.

Usage:
  python scripts/generate_gmail_oauth_token.py
"""

from __future__ import annotations

import http.server
import json
import socketserver
import urllib.parse
import urllib.request
import webbrowser
import sys

PORT = 8085
REDIRECT_URI = f"http://localhost:{PORT}/oauth2callback"
SCOPE = "https://www.googleapis.com/auth/gmail.send"


class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    auth_code: str | None = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/oauth2callback":
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                OAuthCallbackHandler.auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h1>Authorization successful!</h1><p>You can close this window and return to your terminal.</p>")
            else:
                err = params.get("error", ["Unknown error"])[0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h1>Authorization failed:</h1><p>{err}</p>".encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Quiet logging


def main():
    print("=" * 70)
    print("  HealthAware — Gmail API OAuth 2.0 Token Generator")
    print("=" * 70)

    client_id = input("Enter your Google OAuth Client ID: ").strip()
    if not client_id:
        print("Error: Client ID is required.")
        sys.exit(1)

    client_secret = input("Enter your Google OAuth Client Secret: ").strip()
    if not client_secret:
        print("Error: Client Secret is required.")
        sys.exit(1)

    sender_email = input("Enter your sending Gmail address (e.g. sreemani0323@gmail.com): ").strip()

    # Construct Authorization URL
    auth_params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(auth_params)}"

    print("\n1. Starting local authorization listener on port", PORT, "...")
    print("2. Opening your browser for Google consent:")
    print(f"   {auth_url}\n")

    try:
        webbrowser.open(auth_url)
    except Exception:
        print("Please copy the URL above and open it in your web browser.")

    with socketserver.TCPServer(("", PORT), OAuthCallbackHandler) as httpd:
        print("Waiting for OAuth authorization callback from Google...")
        while OAuthCallbackHandler.auth_code is None:
            httpd.handle_request()

    code = OAuthCallbackHandler.auth_code
    print("\nAuthorization code received! Exchanging code for refresh token...")

    # Exchange code for refresh token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    req = urllib.request.Request(token_url, data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"})

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"\nFailed to exchange code: HTTP {e.code} - {e.read().decode('utf-8')}")
        sys.exit(1)

    refresh_token = data.get("refresh_token")
    if not refresh_token:
        print("\nNotice: Google did not return a refresh_token in this exchange.")
        print("This happens if consent was already granted without prompt=consent.")
        print("Token response:", json.dumps(data, indent=2))
        sys.exit(1)

    print("\n" + "=" * 70)
    print("  SUCCESS! COPY AND PASTE THESE INTO RENDER DASHBOARD ENVIRONMENT:")
    print("=" * 70)
    print(f"GMAIL_CLIENT_ID={client_id}")
    print(f"GMAIL_CLIENT_SECRET={client_secret}")
    print(f"GMAIL_REFRESH_TOKEN={refresh_token}")
    if sender_email:
        print(f"GMAIL_SENDER_EMAIL={sender_email}")
    print("=" * 70)


if __name__ == "__main__":
    main()
