#!/usr/bin/env python3
"""
Run ONCE locally to generate Gmail OAuth2 token.
The output JSON goes into GitHub Secret: GMAIL_TOKEN_JSON

Prerequisites:
  1. Go to https://console.cloud.google.com
  2. Create a project → Enable Gmail API
  3. Create OAuth 2.0 credentials (Desktop app type)
  4. Download the JSON → save as credentials.json in this directory

Then run:
  pip install google-auth google-auth-oauthlib google-api-python-client
  python3 .github/scripts/gmail_auth_setup.py
"""
import json
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
]

creds_file = Path("credentials.json")
if not creds_file.exists():
    print("ERROR: credentials.json not found in current directory.")
    print("Download it from Google Cloud Console → APIs & Services → Credentials")
    exit(1)

from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
creds = flow.run_local_server(port=0)

token_data = {
    "token":         creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri":     creds.token_uri,
    "client_id":     creds.client_id,
    "client_secret": creds.client_secret,
    "scopes":        list(creds.scopes)
}

output = json.dumps(token_data)

print("\n" + "="*70)
print("SUCCESS! Copy this value into GitHub Secret: GMAIL_TOKEN_JSON")
print("="*70)
print(output)
print("="*70)
print("\nAlso set: GMAIL_USER_EMAIL = your Gmail address")
