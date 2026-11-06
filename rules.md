# Rules page

One place for every rule and every fix, with the date and who decided (Erin, Nov 2: "when Owen says 'I never agreed to that' I can point to it"). Add a line when something changes. The code follows this page.

| Date | Who decided | Rule |
|---|---|---|
| 2026-11-02 | Erin, Owen | A real conversation is a scan with a note or a star, a card, a voice note or a line on Owen's list. A star alone means Owen talked to them. |
| 2026-11-02 | Owen | "draw", "swag", "didn't talk", "said hi" means no conversation, whoever they are. |
| 2026-11-02 | Owen, Erin | No draft for competitors' reps, suppliers, event staff or students (unless Owen noted something). Existing customers: Owen phones them; Erin spots them by clinic name. |
| 2026-11-02 | Nadia, Owen | Hot = we promised something specific: demo, pricing, trial or a call back. "Send me some info" is not a promise. A question mark ("demo?") is not an ask. |
| 2026-11-04 | Nadia | A specific document (a security sheet, say) is owed and goes out with the promises, but the person stays warm, not hot. If the document doesn't exist, the draft can't pretend; Owen calls. |
| 2026-11-02 | recount, Nadia, Owen | Warm = two or more clinics, or paying for Clinivo, Bookstead or Pracshift. Cold = everyone else. Within warm, Owen ranks by clinics and Nadia by paid software; the page shows both and nobody is re-ranked. |
| 2026-11-02 | Owen | Stars mean clinic count only: A three or more, B two, C one. A missing star means nothing. |
| 2026-11-02 | Owen | Voice note beats scan note; voice notes and the list agree with each other. A real disagreement is flagged, not guessed, and the source chosen is written down. |
| 2026-11-02 | Owen | A list line the tool can't place is flagged with the best guesses, never skipped. |
| 2026-11-04 | Nadia | Scanned on Nadia's phone with nothing else: draft is prepared, sender is flagged "was this you?". Nadia claims it or passes it to Owen. Never sent under a guessed name. |
| 2026-11-04 | Nadia | Whoever's notes hold the promise sends. If both wrote something substantive, flag it for Nadia and Owen to decide. Never two senders. |
| 2026-11-02 | Owen, Nadia | Card email beats badge email. If it bounces, use the badge email and say so. |
| 2026-11-02 | Erin, Nadia | All drafts cc hello. The cc is how "sent" is known; a second run skips anyone already sent. |
| 2026-11-02 | Erin, Nadia | Nobody with N on the share flag gets a draft, card or not. They sit flagged until someone who knows the law says where the line is. Nadia owns getting that answer (Nov 4). |
| 2026-11-04 | Nadia | Badge scans never go on the newsletter. |
| 2026-11-02 | Erin, Nadia | Anyone who asks to be removed stays off for every show (`memory.csv`). |
| 2026-11-02 | Owen (Amira) | "No mailing list, just pricing" means one plain reply with the pricing and nothing else. |
| 2026-11-02 | Owen, Nadia | Each draft does only what was asked: demo gets a way to book, pricing gets the numbers ($34 per practitioner a month), trial gets the sign-up link plus "I'm around if you get stuck", send info gets the one-pager and the price, thank-you is two lines that mention the one thing they said. |
| 2026-11-02 | Owen | Call back is a reminder for the phone, not an email. Shauna gets no demo link. |
| 2026-11-02 | Owen | Two asks in one conversation: one draft, the firm ask first, the questioned one as one extra line. |
| 2026-11-02 | Owen | Draft shape: "Steve, good to meet you in Toronto", the one thing we talked about, what they asked for, Owen. Three or four lines. No "I hope this finds you well", no "pleasure connecting", no feature paragraphs. |
| 2026-11-02 | Owen, Nadia, Erin | Personal remarks (family, health, pets, who knows Sam) never go in a draft, to any AI tool, or into anything Erin keeps. They are dropped when the notes are read. |
| 2026-11-04 | Nadia | Someone who said "maybe next year" and was a real conversation gets a two-line thank-you with no link, after the promises. |
| 2026-11-02 | Erin | Someone who already booked a demo gets no "book a demo" link; they count as booked. |
| 2026-11-02 | Erin, Owen, Nadia | A generic note more than three weeks after the show is pointless and is not drafted. A promise never expires: "Sorry this took me a while, here's what you asked for." |
| 2026-11-04 | Nadia | French only for people Nadia actually spoke French with (Hélène, Sophie). Never from a card or a job title. Owen can flag someone and pass them to Nadia. |
| 2026-11-02 | Owen | Order on Owen's phone: promises and owed documents first, then groups, then two-clinic places, then singles. |
| 2026-11-02 | Nadia, Erin, Owen | Four piles at day 30: booked a demo (booked by day 30 counts, held or not), started a trial, written to with no reply, never written to. Counts with names. Same shape for every show so Toronto and Moncton sit side by side. |
| 2026-11-02 | Erin, Owen | A booking or trial from the same clinic after the show counts, whoever typed it, and the reason for the match is shown. "Google", "Instagram", "podcast" bookings are not from the show. |
| 2026-11-02 | Erin | Links, the one-pager and the hello address are set once by Erin on the upload page (Links) and kept for every show. Until then a draft shows a yellow marker such as `[one-pager link]`, never a blank. |
| 2026-11-04 | Nadia | Demo link is Nadia's calendar only. Nothing assumes Owen takes demos. |
| 2026-11-04 | Nadia | AI is optional. The core is rules, so Sam has less to approve. If an AI service is ever used, the account doesn't sit on a personal login, and Owen's personal remarks never reach it. Test: if Owen has to rewrite a draft, it failed. |

## Fixes

| Date | Who | What changed |
|---|---|---|
| 2026-11-05 | Neo (build) | Page redone: one sentence, one number, one action per view; drafts and reasons open on a tap; no hot/warm/cold labels on the page (they stay in `people.csv`). Rules and results unchanged. |
| 2026-11-05 | Neo (build) | Someone on the do-not-email list still counts as a conversation for the four piles; they just never get a draft. |
| 2026-11-05 | Neo (build) | Security document not set → no draft; Owen gets a call reminder (Nadia, Nov 4). |
| 2026-11-05 | Neo (Moncton mock) | A named document (SOC2, security spec) is owed even when nobody wrote "send me": next step is send info. |
| 2026-11-05 | Neo (Moncton mock) | "Do not push a demo now", "no demo yet" cancel the demo word; "call mid-Nov", "reminder to call her around the 15th" are call-backs, with the month on the reminder. |
| 2026-11-05 | Neo (Moncton mock) | "Took a pen", "saying hi", "came by again" are drive-bys. "Looking forward to our Tuesday call" means already in touch: no draft. |
| 2026-11-05 | Neo (Moncton mock) | A booking or email dated before the show is not from the show (goes to activity-not-from-show.csv). |
| 2026-11-05 | Neo (Moncton mock) | A bounced address falls back to the other address on file, flagged for Erin; no other address → Owen phones. |
| 2026-11-05 | Neo (Moncton mock) | "Dr." in the first-name column is a title, not a name. |
| 2026-11-05 | Neo (Moncton mock) | Show files can be CSV, Excel sheets or JSON; each table is recognised by its header (scans, cards, voice notes, list, after-show). Unrecognised sheets are listed in the run report and ignored. |
| 2026-11-06 | Neo (merge) | "Pricing but in writing" stays a pricing ask (hot): Erin's recount has Tyler Brennan hot, and his voice note asks for pricing. The draft gives the number in writing. |
| 2026-11-06 | Neo (stress fixes) | Consent is its own gate. Anyone with N on the share flag is held, including people who asked for something at the booth (Erin and Nadia: hold N until someone who knows the law decides). This changes Amira Haddad from a plain reply to a hold. **Nadia to confirm**, since Erin also said Amira gets a plain reply. |
| 2026-11-06 | Neo (stress fixes) | Do-not-email checks run in order: address, name and clinic, close name and close clinic. A confirmed match has no draft and can't be released. Same name at another clinic, or a close name, is "might be": no draft until Erin presses Same or Different. Same name alone is never called a match. |
| 2026-11-06 | Neo (stress fixes) | A reply or a note that says stop, or withdraws permission, puts them on the list for every show. |
| 2026-11-06 | Neo (stress fixes) | Dates: an event counts from the first scan to exactly 30 days after the last scan, end included. Events during the show count. **Nadia to confirm**: the written request said only after the show. Times are read as written, in the show's local time; an offset is dropped, not converted. A date with no time counts that whole day, and on the first or last day Erin is told. An unreadable date is never counted and always listed. Day and month that could swap are not guessed. |
| 2026-11-06 | Neo (stress fixes) | Emails sent before the show don't count and don't stop a draft. Sent after day 30: not in the piles, but nobody is offered a second email. |
| 2026-11-06 | Neo (stress fixes) | Nothing exported uses the words of a note. Exports are built from facts the tool worked out and its own fixed sentences. Each draft and file is checked again before it's offered. A doubtful draft isn't offered: PRIVACY REVIEW REQUIRED. "Business partner" is business. |
| 2026-11-06 | Neo (stress fixes) | No usable address (N/A, null, blank, plain text): no draft and no READY. A phone means a call reminder, extension kept. No phone means Erin finds a contact. Full-width characters, spaces, case and "mailto:" are tidied; nothing else is guessed. "Phone only" or "no emails" means a call and no email text. |
| 2026-11-06 | Neo (stress fixes) | A clear "no longer wants it" beats an older ask. A newer clear ask beats an older "no". "Still no demo from Toronto" is an unkept promise, not a withdrawal. |
| 2026-11-06 | Neo (stress fixes) | One sentence naming two people: each gets the words after their own name. If that can't be done ("both want"), or two people share the name and no clinic is given, it goes to neither and a person places it. |
| 2026-11-06 | Neo (stress fixes) | Language comes from the conversation, never from a card or a name. "Spoke in English" means English. Notes saying both are flagged. French goes out from Nadia only. |
| 2026-11-06 | Neo (stress fixes) | Same event from two exports counts once; different times stay separate. Unknown event types aren't counted and are listed. A cancelled booking still counts (booked by day 30 counts), and Erin is told. |
| 2026-11-06 | Neo (stress fixes) | Uploads replace a show's files by default. "Add to" keeps them. Each run records its time and files in `runs.jsonl`. Bad records are listed in `input_issues.csv`; none are dropped silently. |
| 2026-11-06 | Neo | Each email goes from whoever had the conversation, from their own mailbox, cc hello (Nadia and Owen, group call). Erin checks and coordinates and doesn't send. Her page lists what she checks and what she hands to Owen and Nadia, each with an action. |
| 2026-11-06 | Neo (merge) | Moved to one tool: this page's rules on the engine that did best on the made-up shows. Someone removed at an earlier show is matched by name and clinic, not only by address, through `memory.csv`, which replaces `do-not-email.csv`. |
| 2026-11-05 | Neo (Moncton mock) | The one thing they said, when none of Toronto's phrases fit: locations count, spreadsheets/paper, solo, just looking, comparing systems, contract up at year end, security details, opening a second location. Voice note first, then list, card, scan. |
