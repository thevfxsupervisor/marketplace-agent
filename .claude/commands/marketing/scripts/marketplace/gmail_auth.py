#!/usr/bin/env python3
"""
Shared Gmail auth helper for the marketplace-selling scripts, plus a one-time token setup.

Deliberately takes every path as an explicit argument or a required env var, never a hardcoded
default. A hardcoded default path encodes which machine's account layout the script runs on, which
is exactly the kind of thing this skill's leak rules forbid putting in a shared repo. If a required
env var is missing, this fails loudly rather than falling back to a guessed path.

ONE-TIME SETUP (creates the token the other scripts use):
  1. In Google Cloud Console, in a project you control: enable the Gmail API, configure the OAuth
     consent screen (External + yourself as a test user is enough for personal use), then create
     an OAuth client ID of type "Desktop app" and download its JSON. That JSON is the
     "client credentials" file. Keep it outside any repo.
  2. export MKT_GMAIL_CREDENTIALS_PATH=/absolute/path/to/client-credentials.json
     export MKT_GMAIL_TOKEN_PATH=/absolute/path/to/token.json   (does not need to exist yet)
  3. python3 gmail_auth.py --setup
     A browser opens for consent; the token is written to MKT_GMAIL_TOKEN_PATH with mode 0600.
  Scope requested: https://www.googleapis.com/auth/gmail.modify . The watcher ARCHIVES what it
  prints (messages.batchModify), which needs gmail.modify; a gmail.readonly token fails at the
  first archive. gmail.modify cannot permanently delete mail.

Dependencies: google-api-python-client, google-auth, and (for --setup only) google-auth-oauthlib.

Otherwise imported by watch_buyer_messages.py and get_relay_link.py.
"""
import json
import os
import sys

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        print(
            f"Missing required env var {name}. See the module docstrings in this directory "
            "(gmail_auth.py has the one-time token setup).",
            file=sys.stderr,
        )
        sys.exit(1)
    return val


def _load_json(path: str, what: str):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(
            f"{what} not found at {path}. Run `python3 gmail_auth.py --setup` first "
            "(see its docstring).",
            file=sys.stderr,
        )
        sys.exit(1)


def get_gmail_service(token_path: str, credentials_path: str):
    """Build an authenticated Gmail API client from a user OAuth token and a client credentials
    file. Both paths are required arguments; callers must get them from an env var or a config
    file, never a baked-in default."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    token_path = os.path.expanduser(token_path)
    credentials_path = os.path.expanduser(credentials_path)

    t = _load_json(token_path, "Gmail token")
    c = _load_json(credentials_path, "OAuth client credentials")
    c = c.get("installed") or c.get("web") or c
    t.setdefault("client_id", c["client_id"])
    t.setdefault("client_secret", c["client_secret"])
    if "token" not in t and "access_token" in t:
        t["token"] = t["access_token"]

    return build(
        "gmail",
        "v1",
        credentials=Credentials.from_authorized_user_info(t),
        cache_discovery=False,
    )


def setup():
    """Run the OAuth consent flow once and write the user token, mode 0600."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds_path = os.path.expanduser(require_env("MKT_GMAIL_CREDENTIALS_PATH"))
    token_path = os.path.expanduser(require_env("MKT_GMAIL_TOKEN_PATH"))
    _load_json(creds_path, "OAuth client credentials")  # fail early and readably
    creds = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES).run_local_server(port=0)
    fd = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(creds.to_json())
    print(f"Token written to {token_path} (mode 0600), scope gmail.modify.")


if __name__ == "__main__":
    if sys.argv[1:] == ["--setup"]:
        setup()
    else:
        print("Usage: python3 gmail_auth.py --setup   (see the module docstring)", file=sys.stderr)
        sys.exit(2)
