# marketplace-agent

**An AI agent that runs your second-hand sale and gives you back the hours.** The agent writes the listings, watches the inbox,
answers buyers, books pickups and closes ads once things are collected. You stay in charge of
prices, who gets what, and the handover itself.

Built for [Claude Code](https://claude.com/claude-code) and tested on a real ten-day sale on
[DBA.dk](https://www.dba.dk) (a Danish second-hand marketplace) and Facebook Marketplace.
The write-up of how that went, with the numbers, is on my site:
[My agent sold my old furniture and saved me more than 70 hours](https://thevfxsupervisor.com/notes/selling-stuff-with-an-agent/).

## What the agent does

- **Lists items** in the local language, with the right category and condition, and checks every
  ad on the public page after posting rather than trusting that the form saved.
- **Watches buyer messages** through the platforms' email relays and surfaces only what needs a
  decision.
- **Answers the routine questions** once you have set the policy: is it still available, when,
  where, how to pay.
- **Keeps one list** of who was promised what, with a named backup for every item, so a no-show is
  one message away from a sale.
- **Closes the loop:** marks ads sold or given away after pickup and tells the backups it has gone.
- **Spots the scam pattern** ("still available?" followed by a courier or off-platform payment
  pitch) and stops engaging.

## What it does not do

The agent does not set prices or accept offers: it proposes, you decide. For free items it can run a first-come list under a rule you agree. It does
not sign in for you or touch payment details. And someone still has to be there for the pickup.

## What is in here

| Path | What it is |
|---|---|
| `.claude/commands/marketing/marketplace-selling.md` | The playbook the agent follows: setup, listing, pricing, replying, booking pickups, marking sold, plus platform mechanics for DBA.dk and Facebook Marketplace as observed in October 2026 |
| `.claude/commands/marketing/scripts/marketplace/` | Small Python scripts: a Gmail-based buyer-message watcher, its polling loop, a one-time Gmail auth helper, and a tool that pulls Facebook's edit/delete links out of relay emails |

## What you need

- [Claude Code](https://claude.com/claude-code).
- A browser-automation tool the agent can drive, such as Claude in Chrome, with you already logged in to DBA.dk and/or Facebook Marketplace. The agent never signs in for you.
- For the inbox watcher: Python 3.9 or newer, `pip install -r requirements.txt`, and a Gmail account that receives the marketplaces' message notifications.
- Check each marketplace's terms before you automate anything on it.

## Install

1. Copy `.claude/commands/marketing/` into `~/.claude/commands/` (or into a project's
   `.claude/commands/`). Claude Code then offers `/marketing:marketplace-selling`.
2. For the inbox watcher, follow **Scripts and setup** in the playbook: a Gmail API OAuth client
   of your own, three environment variables, and `gmail_auth.py --setup` once. Nothing in this repo
   holds credentials, and a missing variable fails loudly rather than guessing a path.
3. Start a sale: `/marketing:marketplace-selling ~/sales/my-sale` and talk to it.

Marketplace sites change their pages often. Treat the platform notes as a starting point and let
the agent verify each action on the public page, which the playbook already insists on.

## About

Made by Geoffrey Hancock, VFX supervisor and producer, who builds production pipelines and puts AI
agents to work on the parts of a job nobody should be doing by hand.
[thevfxsupervisor.com](https://thevfxsupervisor.com)

MIT licensed.
