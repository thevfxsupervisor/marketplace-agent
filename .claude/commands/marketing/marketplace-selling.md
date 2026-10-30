---
description: Run and track a sale on DBA.dk and/or Facebook Marketplace - listing mechanics, pricing ladder, buyer-message watching, pickup booking without over-promising a helper's time, marking sold, and a reversible tracker. Argument is the sale's project folder (defaults to the current directory).
---

# /marketing:marketplace-selling - sell second-hand items on DBA and Facebook

**Why this exists.** Selling more than a couple of items turns into a flood of near-identical buyer
messages, reused photos, and pickup slots that collide with whoever actually staffs the handover.
The mechanics (shadow-DOM forms, Danish-letter typing traps, token-only edit links) are fiddly
enough to relearn every time without a reference. This skill is that reference plus the guardrails
that kept a real sale from overpromising a helper's time or leaking who bought what.

## Setup: one project folder, one tracker

Pick a sale folder, e.g. `~/projects/<area>/<sale-name>/`. Inside it:

- `STATE.md` - current snapshot only (see "Tracker" below). Rewritten, not appended to.
- `ADS.md` - append-only chronological log: every ad created or edited, every buyer reply, every
  decision. Keep the full history here, not in STATE.md, so the snapshot stays short enough to
  actually read before acting.
- `photos/` - source photos, reused across DBA and FB listings of the same item.
- `tools/` - optional: symlink the scripts from this skill's `scripts/marketplace/` dir in here
  (see "Scripts and setup" for where that dir lives once installed, and the env vars they need).

**One writer.** If a human delegate (a partner, a helper, anyone who is not you) also needs
visibility, give them a shared location with exactly one writer: you. A shared doc, canvas, sheet
or channel update edited from one side only, never a resource two people write to at once. Update
it when state actually changes, not on every micro-step.

## Listing an item

The exact click paths for DBA and Facebook Marketplace (create, edit, give away, mark sold,
delete, the Facebook guest-listing cap) are in "Platform specifics" near the end. The rules below
are the platform-independent part.

**Photos first.** Upload photos before filling the text fields; some create flows render the page
blank right after an image upload. Reload the create URL if that happens.

**Title.** Short, plain, searchable: item plus key spec (e.g. "<brand> <item>, <size>"). Keep
currency and price symbols out of the title; the price field is separate.

**The Danish-letters trap.** Typing æ, ø, å via a simulated keystroke action into a
React-controlled text field can silently scramble the text (observed twice on one platform's
listing form). Prefer:
- Set the field value with the native element's value setter plus a real `input` event, OR
- `document.execCommand('insertText', false, text)` into the VISIBLE input (not a hidden mirror -
  check it has real height and is not `aria-hidden`).

Then **read the value back and verify it matches** before moving on. Never trust a value you only
set and never re-read.

Title fields specifically can reject a pure JS-set value (Continue then fails with "missing
fields") until a real keystroke or click has landed in that field first. If a JS-set value does not
stick, retry with: focus, select-all, `execCommand('insertText')`; or a real click plus an
End/space/BackSpace nudge to force a change event.

**Categories.** Pick the narrowest matching category. A wrong category is one of the few things
that is hard to fix after the fact on some platforms - re-create the listing rather than fight a
broken edit.

**Free vs. paid listing packages.** Create flows often default to a paid promotion package. Before
submitting, check the total and switch to the free tier if that is what you want: walk the flow
through to confirm the final button reads something like "post ad" at a zero total, not "go to
payment".

**Trade type (sell vs. give away) is a real field, not just a price of zero.** If the platform has
a separate "giving away / free" trade type, use it for free items. Posting a giveaway as a paid
listing at a token price (e.g. 1 unit of currency) can get silently rejected, and editing the trade
type on a rejected listing may not revive it - re-create instead of fighting a rejected listing.

**Free backup ads for cheap items.** For low-value items where a paid ad is also running, a second
free-tier "giveaway" ad gives a price-sensitive buyer a no-cost option while the paid ad stays live
for anyone willing to pay. Note which ad is which in your tracker, so you know which one to retire
first once the item moves.

**Number fields (price, postcode, dimensions).** Scripted keystroke commits are fiddly here: a
trailing End+Space+Backspace nudge that commits a text field can instead delete the last digit of a
number field. End a number edit on a real digit, not a space, and verify the saved value on the
PUBLIC listing page afterward - a save can look successful in the editor and not have actually
taken.

**Verify every listing after creating or editing it** by fetching the public listing page, not the
edit form, and checking title, price and key text actually landed.

## Pricing ladder and cuts

- Research several comparable live listings before setting an initial price; note the range, not
  just one number, and date it (comparables age).
- Price with headroom to cut, not at a floor, on day one, unless the owner says otherwise.
- When cutting, mark the title clearly (a "price cut" prefix in the local language) and say in the
  body that the price was reduced - buyers re-find relisted items by that marker. Keep a
  before/after table in your log.
- **Never cut a price without first checking the item has not already sold.** A cut landing on an
  already-sold listing just confuses the next buyer.
- Cut on the owner's go once real money is involved: price is a business decision, mechanics are
  yours to run.

## Deadline and last-pickup wording

- State one explicit last-pickup date in every ad, and keep every live ad's date consistent. A sale
  with dozens of live ads drifts (a typo on one ad, or a changed plan, does not propagate to the
  rest) unless you sweep and re-verify all of them after any date change.
- Get the real last-pickup date from the owner before writing it anywhere. Do not infer it from
  another event's date without confirming, and double-check the day-of-week actually matches the
  calendar date before publishing it on every ad.
- If you are told to drop any mention of WHY the sale is happening (a reason for the sale, an
  organisation name), treat that as a rule for every new ad AND an audit task against existing live
  ads, not just the next ad you write.

## Watching for buyer messages

Buyer messages on both platforms typically arrive by email: a platform-relay email for in-platform
chat, or a dedicated notification mail. Poll that inbox rather than the platform's own notification
UI - mail is scriptable, the platform UI often is not.

Use `scripts/marketplace/watch_buyer_messages.py`: it prints one line per new message, oldest
first, and archives what it printed so the inbox does not refill with things you already saw. It
pages through every match, advances its cursor only to the newest message it actually printed (so a
backlog is never skipped, only spread over ticks with an explicit "N more not shown" line), and
dedupes its small overlap window by message id (so nothing prints twice). Configure it entirely
through env vars - no hardcoded account details, see the script's own header.

Run it on a loop with `scripts/marketplace/watch_monitor.sh`, inside a configurable ACTIVE window
(`MKT_ACTIVE_START` / `MKT_ACTIVE_END`, the hours it polls): do not poll, and do not expect
replies, outside the hours the seller actually answers messages.
**Exactly one monitor per sale** - a second instance racing the same state file double-prints and
can double-archive.

**If the loop was not running (a session restart, a compaction), say so explicitly** when you
resume, and report however many messages piled up as a backlog, not as "nothing new."

## Replying

- **Match the thread by its URL/ID, never by the displayed name.** Auto-translation on some
  platforms translates buyer names in the UI (a displayed name can come out completely different
  from what the buyer actually typed), and clicking between threads in a single-page app can leave
  an OLD thread rendered under a NEW url. Navigate directly to the thread URL and check the header
  before sending anything.
- **Take the buyer's name from the raw notification email, never from a translated page.** The
  email is relayed from the platform and is not run through the browser's auto-translate.
- Reply in-thread on the platform's own chat where that exists. Where the platform only offers an
  email relay (a guest/email-based listing), reply by email, and treat any per-listing edit/delete
  link inside those relay emails as a secret: never paste it anywhere visible, keep it only in your
  own scratch space for the life of the task. `get_relay_link.py` writes it to a 0600 file and
  prints only the path. Note the limit of that: if you then read the file or hand the URL to a
  browser tool inside an agent session, the URL still enters that session's transcript. Keep it out
  of logs, channels and trackers, and delete the file at the end of the sale.
- **Recognise scam patterns and do not engage:** a templated "still available?" from an unlikely
  buyer profile followed by an off-platform courier or payment pitch, or a request to contact
  privately by email outside the platform, sent to several unrelated listings within minutes of
  each other. Ignore and archive; do not reply, do not click anything in the message.
- Pass on facts as facts ("the legs unscrew; bring a wrench"), never as a promise of someone else's
  labour - see Booking pickups.

## Booking pickups

**Get the delegate's actual hours before offering any slot.** If a helper or partner, not you, is
the one who hands items to buyers, get their START and END time for that day BEFORE telling any
buyer a time. Never say "come whenever," and never imply that person will do extra work (carry
something down, disassemble something) they have not agreed to. A buyer slot is only as good as the
helper's confirmed window - get it fresh each day, not once at the start.

**State FREE or PAID and the amount in every pickup note to a delegate.** When an item has both a
paid listing and a free "giveaway" backup listing live at once, a helper cannot tell by looking
which applies to a given buyer. Always write it out: "<ITEM>, FREE" or "<ITEM>, PAID <amount>".

**A delegate's go counts, when the owner has said so.** The owner may authorise someone else (a
partner, a trusted helper) to make real-time calls on prices, buyers and pickup times in their own
channel, with the same weight as the owner's own word. Keep that person updated there and act on
their corrections; the authorisation does not extend past the scope it was given for.

**Do not tell other buyers an item is sold until it is actually collected.** A verbal "yes" or an
agreed price is not the item leaving the building; a deal can fall through at pickup. Say "reserved
for someone collecting <day>" rather than "sold" until collection is confirmed.

**Confirm collection before marking anything sold in your tracker or on the platform.** Get that
confirmation from whoever was actually present at pickup, not from your own assumption that a
confirmed slot means it happened.

## Marking sold / given away

- Mark the item sold (or "given away," where the platform distinguishes the two) only after
  confirmed collection.
- If the platform offers a reversible "mark as sold" (undo available), prefer it over an
  irreversible delete, in case the sale falls through after you mark it.
- Act on EVERY live listing of that item, including a free "backup" ad alongside a paid one, so a
  late buyer never chases an item that is actually gone.
- Log the final price, a placeholder buyer identifier, and the date in `ADS.md`.

## Tracker

Keep `STATE.md` to a current snapshot, roughly:

```
# <Sale name> - STATE
> one-line status, last-pickup date, pointer to the full log

## Who staffs pickups (fixed slots only)
<delegate>: <days/hours>, hard stop <time>

## Bookings (open)
| When | Buyer | Item | Price | Status |

## Sold / collected
<dated list, oldest or newest first - pick one and stay consistent>

## Live ads
<item -> platform ids/urls -> price, grouped so you can sweep them for a global change>

## Rules learned
<anything sale-specific that does not belong in this skill file>
```

## Scripts and setup

**Where the scripts are.** In this repo they sit beside this file at
`.claude/commands/marketing/scripts/marketplace/`. If you install by copying the
category into `~/.claude/commands/`, they are at `~/.claude/commands/marketing/scripts/marketplace/`.
Resolve the real path once, then use absolute paths from the sale folder:

    ls ~/.claude/commands/marketing/scripts/marketplace/ 2>/dev/null \
      || find ~ -maxdepth 7 -type d -path '*commands/marketing/scripts/marketplace' 2>/dev/null

**Gmail token, once per account.** Every script reads mail through the Gmail API with a user OAuth
token:

1. In Google Cloud Console, in a project you control: enable the Gmail API, configure the OAuth
   consent screen (External, with yourself as a test user, is enough for personal use), and create
   an OAuth client ID of type **Desktop app**. Download its JSON: that is the client credentials
   file. Keep it, and the token, outside any repo.
2. Install `google-api-python-client`, `google-auth` and `google-auth-oauthlib`.
3. Export the paths (absolute; put them in a local, never-committed env file you `source`):

       export MKT_GMAIL_CREDENTIALS_PATH=/abs/path/client-credentials.json
       export MKT_GMAIL_TOKEN_PATH=/abs/path/token.json
       export MKT_STATE_FILE=/abs/path/to/sale/tools/watch.state

4. `python3 <scripts dir>/gmail_auth.py --setup` opens the consent page and writes the token with
   mode 0600. **Scope: `gmail.modify`.** The watcher archives what it prints, which a
   `gmail.readonly` token cannot do (it fails at the first archive). `gmail.modify` cannot
   permanently delete mail.

**The scripts.**
- `watch_buyer_messages.py` - one tick: print and archive new buyer-relay mail. Header lists every
  optional knob (sender query, overlap, per-tick cap, fetch delay, archive toggle).
- `watch_monitor.sh` - the loop around it, inside the active window. Resolves the watcher from its
  own location, so it works from any directory. Exactly one per sale.
- `get_relay_link.py` - pull an edit/delete token link out of a relay email into a 0600 file
  (`--out FILE`, `--open`, or `--print` if you accept it being logged).
- `gmail_auth.py` - shared auth plus the `--setup` above.

**Gmail quota.** Fetching many full messages back to back hits the per-minute quota (403
`rateLimitExceeded`). Space full-message gets about 0.4 s apart; the watcher's metadata gets default
to 0.25 s (`MKT_GET_DELAY`).

## Platform specifics (as observed October 2026)

These are public site mechanics, observed driving the sites through a browser-automation tool.
Sites change: treat each as a first thing to try, and verify on the public page afterwards.

**DBA.dk**
- **Create:** `dba.dk/create-item/start`, then a REAL click on the "Markedspladsen" (marketplace)
  card (a web component inside shadow DOM). Upload photos, then RELOAD the create URL (the form can
  render blank after an upload). Category, subcategory, product type and condition are native
  selects inside shadow roots: set the value plus a `change` event, and wait about 1.5 s between
  levels.
- **Title:** must be entered with real keystrokes; a JS-set title does not register and Continue
  fails with "Category and N other fields". Add Danish letters afterwards with
  `setSelectionRange` plus `execCommand('insertText')`. On a title EDIT where keystrokes do not land,
  `focus(); select(); execCommand('insertText', false, newTitle)` does register.
- **Description:** after a photo upload a per-photo "Caption" textarea appears BEFORE the
  description. Pick the textarea whose placeholder is not "Caption", or the text lands in the caption.
- **Number fields** (price, postcode, and dimensions in some categories) vary by category: pick them
  by the field's label, not by position. An End/space/BackSpace nudge deletes the last digit; end on
  a digit instead. A password-manager icon can sit in the postcode field: click left of it.
- **Brand field** only accepts a value picked from its list; leave it empty rather than fight it.
- **Giving away:** choose the "Gives væk" (given away) trade type at the top of the form; the price
  field disappears. The radio needs a JS click on the input inside its shadow root. A "sell" ad at
  a token price gets rejected for wrong trade type, and editing the type on a rejected ad does not
  revive it: re-create.
- **Finish the flow:** Continue (the Danish UI says "Fortsæt") twice, "I can't send the item" for a
  pickup-only sale, then the Basis package (click its label card until the total reads 0 kr and the
  button reads "Opret annoncen" (create the ad)). Wait for the publish click to land before
  navigating away, or a stale draft appears.
- **Clicking:** `scrollIntoView({block: 'center'})` before any coordinate click; `'start'` puts the
  field under the sticky top bar and the click hits the navigation.
- **Edit:** `dba.dk/recommerce/create/<adId>`. After a nudge the first Save click can do nothing:
  click Save twice, then submit on the delivery page.
- **Verify:** fetch the public item page (`dba.dk/recommerce/forsale/item/<adId>`) with curl and
  check title, price and key text. It can lag a minute after a save: recheck before calling it
  failed.
- **Mark sold:** `dba.dk/my-items/details/<adId>`, "Mark as sold", then "Not now" on the review
  page ("Go back" when there was no chat). Reversible ("Remove sold mark"), so prefer it to deleting.
- **Chat:** the composer has a hidden mirror textarea; `execCommand('insertText')` into the VISIBLE
  one (real height, not `aria-hidden`) works and keeps Danish letters. One photo per message. Verify
  by the text appearing in-thread and the composer emptying. A thread missing from the inbox list
  can be opened from the `dba.dk/messages/id/...` link in its notification email.
- **Price research:** public search pages carry JSON-LD with each item's name and `offers.price`,
  so a curl of the search URL gives quick comparables without a browser.
- **Trade type is fixed once live.** A live "Gives væk" ad cannot be switched to "Sælges" (sell),
  or back: Save fails with "The update is not valid on an active product". To price a free item
  (or free a priced one), create a FRESH ad in the right trade type and mark the old one given
  away. A fresh free ad also reaches the people who browse the free category.
- **Promised items:** prefix the title with "RESERVERET:" (reserved) the moment an item is promised.
  It cuts the flood of "is it still available?" messages without closing the ad.
- **Package page check:** read the main button before clicking. "Gå til betaling" / "Go to
  payment" means no package, or a paid one, is selected. JS-`click()` the Basis W-CARD, re-read the
  button until it says "Opret annoncen" / "Create the ad", then click it.
- **Read receipts:** a chat message shows "Sendt" (sent) until opened and "Set" (seen) after. An
  offer still at "Sendt" has not been declined, it has not been read; say so before reallocating.
- **Leftovers:** for the last-day pile, one free ad listing everything, placed outside, with "just
  take it, no need to write", saves a dozen chats.

**Facebook Marketplace (guest/email listing)**
- **Create** at `facebook.com/marketplace/create/item`. Publishing sends a verify email: take the
  "Verify email address" link's href from the email's HTML part via the Gmail API (the plain-text
  part drops hrefs), open it, then click "Publish listing". Price 0 is accepted.
- **Listing limit:** guest listings are capped. When create redirects to
  `/marketplace/np/create/limit_reached/`, no more can be created that way; plan for the other
  platform to carry the rest.
- **Edit** only through the token link in the "published"/"updated" email (the normal edit URL
  404s). After opening it, wait about 6 to 7 s before running any JS: it redirects mid-load and a
  script run during the redirect fails. The price field shows "NN kr."; set it by focus, select-all
  and typing the full number.
- **No "mark as sold"** on a guest listing, only Delete: the same emails carry
  `action=delete` links. Pick by listing id AND action, never the first href (one was a "report"
  link). Open it, wait, then a REAL click on the dialog's "Delete listing" button (a JS `.click()`
  does nothing). Success is a redirect with a delete marker plus a "Your listing has been deleted"
  email.

## Operating notes (learned on a live sale)

- **Keep a named backup for every promised item.** When the first buyer collects, tell each backup
  at once that it is gone; when the first buyer no-shows, the backup is one message away.
- **Gmail API rate limits:** many per-buyer thread lookups in a burst can trip a 403 quota error
  inside the watcher. Space lookups out; the watcher recovers on its next poll.
- **After a reboot:** the browser session may be logged out, and more than one browser extension
  may be connected. Find the one the seller is logged in to and select it; never sign in for
  them. Keep helper scripts in the project folder, not a temp directory, or a reboot wipes them.
- **A late buyer is not a no-show:** check the chat before reallocating, and give one clear
  deadline ("today until 15:00, otherwise Saturday 12-17") rather than open-ended waiting.

## End-of-sale cleanup

- Sweep every platform for listings that are still live but should be sold or removed.
- Let expire, or otherwise stop holding, anything you treated as a secret (edit/delete token
  links).
- Stop the buyer-message monitor loop.
- Fold any durable, reusable lesson (a new platform mechanic, a new scam pattern) back into this
  skill file, generalised, with no names, amounts or ids tied to this specific sale.

## Leak discipline

Never record, in this skill file, in a shared log, or anywhere outside your own private sale
tracker: real buyer names, phone numbers, emails or addresses, buzzer or door names, organisation
names, partner or delegate names, chat or channel IDs, canvas or doc IDs, ad or listing IDs, email
message IDs, or any credential or token path that reveals account structure. Use placeholders:
`<BUYER>`, `<HELPER>`, `<ADDRESS>`, `<ITEM>`. Keep real identifiers only in your own private project
files, never in a skill, a public repo, or a shared channel.
