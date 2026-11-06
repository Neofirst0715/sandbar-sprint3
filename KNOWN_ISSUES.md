# Known issues

Last updated 2026-11-06, after the stress fixes.

## Needs a decision from Sandbar

| Item | What the tool does now | Who decides |
|---|---|---|
| N-flag people who asked for something at the booth, like Amira | Held, with the ask shown to Erin. Erin also said on Nov 2 that Amira gets a plain reply, so this changes what she expected. Needs someone who knows the law | Nadia |
| Bookings made during the show | Counted, because "booked by day 30 counts". The written request said only after the show. None of the three test shows has one | Nadia |
| Same name at a different clinic | No draft until Erin presses Same or Different. Safe, but some real people wait | Erin |
| Cancelled bookings | Still counted in the piles, and Erin is told | Nadia |
| Who changes the program when rules or formats change | Nobody is named. This is the biggest gap | Nadia |

## Not tested

- Double-clicking `start.command` on a Mac. All tests ran on Linux. Try it before the demo.
- `start.bat` on Windows, and Erin's computer, which we still don't know.
- The page on a real phone: Copy and Open in my mail. Checked at phone width in a desktop browser only.
- Dragging files onto the box. Tests upload through the form.
- The Sheet opened in Google Sheets. Only written and read back as a file.
- Whether Owen would send these drafts. He hasn't read them.

## What these tests can't promise

- **Not blind.** I wrote the attack tests after seeing the failures. They stop those failures coming back, but a new show can fail in new ways. The last blind results are 20 of 37 and 43 of 45, and later rule changes haven't had a blind test.
- **New wording is still the most likely miss.** An ask the rules don't recognise becomes a thank-you. On Moncton, one line matches nobody and goes to Owen. On reworded Toronto, Ben's new wording no longer says he asked for anything.
- **Privacy:** exports don't copy notes' words, which is the strong part. Drafts choose from fixed sentences using the notes, so a person should still read every draft. Raw notes stay in `shows/<show>/data`, so that folder must stay restricted.
- **Identity:** two people with very different names and a new clinic can't be linked. Someone who changes name, clinic and address gets through unless a person notices.
- **Time zones:** exports don't state a zone, so times are read as written. A show crossing zones could be off by an hour at the window's edge.
- **Show end:** there's no recorded end time, so the last scan stands in for it.
- **Stop requests by Owen's mailbox:** a "take me off" that reaches only Owen is unseen until he forwards it.
- **Phone decisions:** on a phone or a copy of the page, a button only marks that device. Owen and Nadia tell Erin, or type it in the Sheet.
- **Legal:** the holds follow what Sandbar said to do. None of this is legal advice, and nobody has asked a lawyer.
