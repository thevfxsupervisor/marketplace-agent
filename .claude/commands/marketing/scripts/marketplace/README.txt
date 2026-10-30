marketplace scripts for /marketing:marketplace-selling

Named README.txt on purpose: a .md file anywhere under .claude/commands/ can register as a slash
command. The full setup (Gmail token, env vars, where these files live once installed) is in the
skill file itself, ../../marketplace-selling.md, section "Scripts and setup".

  gmail_auth.py            shared Gmail auth helper; `python3 gmail_auth.py --setup` makes the token
  watch_buyer_messages.py  prints and archives new buyer-relay mail, paginated, cursor-safe, deduped
  watch_monitor.sh         runs the watcher on a loop inside an active window; ONE per sale
  get_relay_link.py        pulls a token edit/delete link from a relay email into a 0600 file

No hardcoded credential or token paths anywhere in this directory. A missing env var is an error
that names it, never a fallback to a guessed path.
