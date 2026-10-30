#!/usr/bin/env python3
"""
Parameterised buyer-message watcher for DBA.dk / Facebook Marketplace (and similar platforms that
relay buyer chat through email).

Prints one line per new buyer-relay message since the last check, oldest first, then (optionally)
archives what it printed, so the inbox does not refill with messages you already saw.

How it avoids both replaying and silently skipping:
- It pages through EVERY match (Gmail nextPageToken), not just the first page.
- The cursor in the state file only advances to the newest message it actually PRINTED, never to
  "now". If a tick is capped (MKT_MAX_PER_TICK), it says how many were held back and they print on
  the next tick.
- The query looks back a small overlap window before the cursor (Gmail's after: is second-granular
  and indexing can lag), and every message id printed inside that window is remembered in the state
  file, so the overlap never prints the same message twice, whether or not archiving is on.
- The "checked since HH:MM" line makes a restart, and the size of any backlog, visible.

Required env vars (no defaults, no fallbacks - this script refuses to run with a baked-in path):
  MKT_GMAIL_TOKEN_PATH        path to the OAuth user token JSON (create it: gmail_auth.py --setup)
  MKT_GMAIL_CREDENTIALS_PATH  path to the OAuth client credentials JSON
  MKT_STATE_FILE              path to a small JSON file this script uses as its cursor

Optional env vars:
  MKT_SENDER_QUERY        Gmail search fragment identifying marketplace senders (default covers
                           DBA.dk and Facebook Marketplace relay mail; these are public platform
                           domains, not account-identifying, so a default here is fine)
  MKT_EXCLUDE_QUERY        Gmail search fragment to exclude noise (default excludes your own
                           outgoing mail and platform publish/verify/update confirmations)
  MKT_LOOKBACK_SECONDS     seconds to look back on the very first run (default 3600)
  MKT_OVERLAP_SECONDS      overlap window before the cursor, deduped by message id (default 120)
  MKT_MAX_PER_TICK         most messages printed in one tick; the rest wait for the next tick and
                           are reported as "N more not shown" (default 50)
  MKT_GET_DELAY            seconds between per-message metadata fetches, to stay under Gmail's
                           per-minute quota (default 0.25)
  MKT_ARCHIVE_AFTER_READ   "1" to remove the INBOX label from every message this tick printed,
                           "0" to leave the inbox untouched (default "1")

Usage: python3 watch_buyer_messages.py
"""
import html
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gmail_auth import get_gmail_service, require_env  # noqa: E402

TOKEN_PATH = require_env("MKT_GMAIL_TOKEN_PATH")
CREDS_PATH = require_env("MKT_GMAIL_CREDENTIALS_PATH")
STATE_FILE = require_env("MKT_STATE_FILE")

SENDER_QUERY = os.environ.get(
    "MKT_SENDER_QUERY",
    '(from:dba.dk OR subject:"on Marketplace" OR from:facebookmail.com)',
)
EXCLUDE_QUERY = os.environ.get(
    "MKT_EXCLUDE_QUERY",
    "-from:me -subject:published -subject:verify -subject:updated",
)
LOOKBACK_SECONDS = int(os.environ.get("MKT_LOOKBACK_SECONDS", "3600"))
OVERLAP_SECONDS = int(os.environ.get("MKT_OVERLAP_SECONDS", "120"))
MAX_PER_TICK = int(os.environ.get("MKT_MAX_PER_TICK", "50"))
GET_DELAY = float(os.environ.get("MKT_GET_DELAY", "0.25"))
ARCHIVE_AFTER_READ = os.environ.get("MKT_ARCHIVE_AFTER_READ", "1") == "1"


def load_state(path):
    """Return (cursor_seconds, {msg_id: internal_seconds}). Accepts the old plain-integer format."""
    if not os.path.exists(path):
        return int(time.time()) - LOOKBACK_SECONDS, {}
    raw = open(path).read().strip()
    try:
        st = json.loads(raw)
    except ValueError:
        st = raw
    if isinstance(st, int) or (isinstance(st, str) and st.isdigit()):
        return int(st), {}
    return int(st["last"]), {k: int(v) for k, v in st.get("recent", {}).items()}


def save_state(path, last, recent):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"last": last, "recent": recent}, f)
    os.replace(tmp, path)


def list_all_ids(g, q):
    """Every matching message id, following nextPageToken until it runs out."""
    ids, token = [], None
    while True:
        kw = {"userId": "me", "q": q, "maxResults": 500}
        if token:
            kw["pageToken"] = token
        r = g.users().messages().list(**kw).execute()
        ids.extend(m["id"] for m in r.get("messages", []))
        token = r.get("nextPageToken")
        if not token:
            return ids


def main():
    g = get_gmail_service(TOKEN_PATH, CREDS_PATH)

    state_path = os.path.expanduser(STATE_FILE)
    last, recent = load_state(state_path)
    since = last - OVERLAP_SECONDS

    q = f"after:{since} {SENDER_QUERY} {EXCLUDE_QUERY}"
    # Gmail lists newest first; reverse so a capped tick prints the OLDEST and the cursor never
    # jumps over a message that has not been printed yet.
    ids = [i for i in reversed(list_all_ids(g, q)) if i not in recent]

    printed = []  # (id, internal_seconds)
    held_back = 0
    for n, mid in enumerate(ids):
        if len(printed) >= MAX_PER_TICK:
            held_back = len(ids) - n
            break
        d = (
            g.users()
            .messages()
            .get(
                userId="me",
                id=mid,
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            )
            .execute()
        )
        if GET_DELAY:
            time.sleep(GET_DELAY)
        ts = int(d["internalDate"]) // 1000
        if ts < since:
            continue
        h = {x["name"]: x["value"] for x in d["payload"]["headers"]}
        printed.append((mid, ts))
        print(
            "==",
            h.get("Date", "")[:25],
            "|",
            h.get("From", "")[:28],
            "|",
            h.get("Subject", "")[:50],
            "|",
            html.unescape(d.get("snippet", ""))[:240],
        )

    if printed and ARCHIVE_AFTER_READ:
        g.users().messages().batchModify(
            userId="me", body={"ids": [m for m, _ in printed], "removeLabelIds": ["INBOX"]}
        ).execute()
        print("archived", len(printed))

    if held_back:
        print(f"{held_back} more not shown (cap MKT_MAX_PER_TICK={MAX_PER_TICK}); next tick prints them")

    # Advance only as far as what was printed. With nothing printed the cursor stays put.
    new_last = max([last] + [ts for _, ts in printed])
    recent.update({m: ts for m, ts in printed})
    recent = {m: ts for m, ts in recent.items() if ts >= new_last - OVERLAP_SECONDS}
    save_state(state_path, new_last, recent)
    print("checked since", time.strftime("%H:%M", time.localtime(since)))


if __name__ == "__main__":
    main()
