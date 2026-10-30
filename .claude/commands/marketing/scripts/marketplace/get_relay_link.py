#!/usr/bin/env python3
"""
Pull a token action link (edit, delete, etc) out of a marketplace relay email.

Generalises a pattern seen on guest/email-based Marketplace listings: the platform's
"listing published/updated" email contains anchor links whose visible TEXT names the action
("Edit listing", "Delete listing", ...). The listing's own normal edit URL can 404; only the link
inside this email works. Treat the link as a secret for the life of the task: never
paste it into a shared channel, a log, or a committed file.

By default the link is NOT printed: it is written to a fresh file with mode 0600 and only that
file's PATH is printed, because anything a script prints inside an agent session lands in the tool
output and the session transcript. Options: --out FILE (write there, 0600), --open (hand it to the
system browser), or --print (stdout, only when you are outside an agent session and accept that).
Delete the file when the task is done.

When an email contains several matching links (one real case had an unrelated "report this" link
land first), use --href-contains to pick the right one by a fragment of the URL itself, such as a
specific listing id or action=delete, rather than trusting link order.

Required env vars:
  MKT_GMAIL_TOKEN_PATH
  MKT_GMAIL_CREDENTIALS_PATH

Usage:
  python3 get_relay_link.py --sender-domain marketplace.facebook.com \
      --subject-contains "<subject substring>" --anchor-text "Edit listing" \
      [--href-contains "listing_id=<id>"] [--newer-than 1h] [--retries 6] [--retry-wait 10]
      [--out FILE | --open | --print]
"""
import argparse
import base64
import html
import os
import re
import sys
import tempfile
import time
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gmail_auth import get_gmail_service, require_env  # noqa: E402


def walk_html(payload):
    if payload.get("mimeType") == "text/html" and payload.get("body", {}).get("data"):
        yield base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf8", "ignore")
    for part in payload.get("parts", []) or []:
        yield from walk_html(part)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sender-domain", required=True, help="e.g. marketplace.facebook.com")
    ap.add_argument("--subject-contains", required=True, help="substring to match in the Subject header")
    ap.add_argument(
        "--anchor-text", required=True, help='substring of the link TEXT, e.g. "Edit listing"'
    )
    ap.add_argument(
        "--href-contains", default=None, help="optional substring the URL itself must contain"
    )
    ap.add_argument("--newer-than", default="1h", help='Gmail "newer_than" value, e.g. 1h, 5d')
    ap.add_argument("--retries", type=int, default=6)
    ap.add_argument("--retry-wait", type=int, default=10)
    dest = ap.add_mutually_exclusive_group()
    dest.add_argument("--out", default=None, help="write the link to this file (mode 0600)")
    dest.add_argument("--open", action="store_true", help="open the link in the system browser")
    dest.add_argument(
        "--print", action="store_true", help="print the link to stdout (logs it in a session)"
    )
    args = ap.parse_args()

    token_path = require_env("MKT_GMAIL_TOKEN_PATH")
    creds_path = require_env("MKT_GMAIL_CREDENTIALS_PATH")
    g = get_gmail_service(token_path, creds_path)

    q = f"from:{args.sender_domain} newer_than:{args.newer_than} subject:({args.subject_contains})"
    msgs = []
    for _ in range(args.retries):
        r = g.users().messages().list(userId="me", q=q).execute()
        msgs = r.get("messages", [])
        if msgs:
            break
        time.sleep(args.retry_wait)

    if not msgs:
        print(f"No message found matching: {q}", file=sys.stderr)
        sys.exit(1)

    m = g.users().messages().get(userId="me", id=msgs[0]["id"], format="full").execute()
    body_html = "".join(walk_html(m["payload"]))

    candidates = []
    for href, text in re.findall(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', body_html, re.S):
        text = html.unescape(re.sub(r"<[^>]+>", "", text))
        if args.anchor_text in text:
            if args.href_contains and args.href_contains not in href:
                continue
            candidates.append(html.unescape(href))

    if not candidates:
        print("No matching link found in the message.", file=sys.stderr)
        sys.exit(1)

    if len(candidates) > 1:
        print(
            f"WARNING: {len(candidates)} links matched; using the first. "
            "Use --href-contains to disambiguate.",
            file=sys.stderr,
        )

    link = candidates[0]
    if args.print:
        print(link)
    elif args.open:
        webbrowser.open(link)
        print("Opened the link in the system browser (not printed).")
    else:
        if args.out:
            path = os.path.abspath(os.path.expanduser(args.out))
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            os.chmod(path, 0o600)
        else:
            fd, path = tempfile.mkstemp(prefix="relay-link-", suffix=".txt")  # mkstemp is 0600
        with os.fdopen(fd, "w") as f:
            f.write(link + "\n")
        print(f"Link written to {path} (mode 0600, not printed). Delete it when done.")


if __name__ == "__main__":
    main()
