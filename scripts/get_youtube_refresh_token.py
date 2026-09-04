#!/usr/bin/env python3
"""
Run this ONCE, locally (not in CI). It opens your browser, you sign in as
complex.spirit and click Allow, and it prints the refresh token to paste
into the YT_REFRESH_TOKEN GitHub secret.

Usage:
    pip install google-auth-oauthlib
    python scripts/get_youtube_refresh_token.py path/to/client_secret_*.json
"""
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    if len(sys.argv) != 2:
        print("Usage: python get_youtube_refresh_token.py <client_secret.json>")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n--- Save these as GitHub repo secrets ---")
    print(f"YT_CLIENT_ID={creds.client_id}")
    print(f"YT_CLIENT_SECRET={creds.client_secret}")
    print(f"YT_REFRESH_TOKEN={creds.refresh_token}")


if __name__ == "__main__":
    main()
