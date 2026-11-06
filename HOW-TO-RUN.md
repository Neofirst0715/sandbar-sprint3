# How to run the after-show station

For Erin, on her first day in after a show. No code. It runs only on this computer and sends nothing.

## Once, before the first show

1. Install Python 3 from python.org if the computer doesn't have it (free). Nothing else is needed.
2. Keep this whole folder in one place only Sandbar staff can open. Don't move `memory.csv` out of it: it remembers who asked to be removed.
3. First run: on the upload page, open **Links** and paste the demo link (Nadia's calendar), trial link, one-pager link and hello address. They're kept for every show. Leave the security document empty if there isn't one: those people get a call from Owen, not a draft that pretends.
4. Make one Google Drive folder that only Nadia, Owen and you can open. Never use "anyone with the link".

## Each show

1. **Check the files arrived.** The scan export, Owen's voice notes and list, and the cards. If something hasn't come, tell Nadia straight out, her cards included.
2. **Open the station.** Double-click `start.command` (Mac; the first time, right-click, then Open) or `start.bat` (Windows). A browser tab opens at `http://localhost:8765`. Keep the small window open while you work; closing it stops the station.
3. **Name the show.** Use the same name for a later run of the same show. Leave **Replace** selected for a normal run.
4. **Drop every file into the box, all at once.** CSV, Excel or JSON, any column names. Each one is recognised by its header. Sheets it doesn't recognise are ignored and named on your page. Any file can be missing; it says what it lost.
5. **Press Run.** The page opens with three buttons: Nadia, Owen, Erin.
6. **Press Erin.** Work down the page. **This run** says what came in. **Check** is yours: each row has an Action. HOLD: LEGAL REVIEW means the badge says N, and nothing you press releases it. HIGH RISK, identity unsure means they might be someone who asked off: press Same person or Different person. **Flags** are for Owen or Nadia: pass each one on, and don't answer it for them. **Ready for follow-up** is theirs to send, from their own mailboxes. **Excluded** is folded: open it to see why. A red "Stop" means don't go on.
7. **Check clinic names against the invoices.** The tool can't tell who's already a customer. Owen phones customers; press Hold for them.
8. **Share it.** Upload `index.html` and `Sandbar_follow_up.xlsx` (Files, at the bottom of your page) to the Drive folder. Tell Owen and Nadia it's ready.
9. **Back up `memory.csv`** to the same folder.

## What each person does

- **Owen:** press Owen. Read each draft, fix a word, press Copy or Open in my mail, send from his own mailbox, cc hello. Promises are at the top. Calls are listed. When someone writes back "take me off", forward it to hello.
- **Nadia:** press Nadia. Her drafts, then "Was this you?", then the four piles at day 30.
- **A decision made on this computer** while the station is running (Mine, Owen sends, Hold) saves and runs the show again. **On a phone or a copy of the page,** the button only marks that device, so they tell Erin, or type it in the Sheet's Decision column. To read a Sheet's decisions: download it as Excel and drop it in with the show's files. Nothing typed can release someone on the do-not-email list or an N flag.

## When Nadia's cards arrive late, or to see who's been written to

Same show name, choose **Add to**, drop the new cards with the cc'd mail: either the activity file or a two-column list (`email`, `date`). Anyone already written to isn't offered again.

## Day 30

Export hello, the booking page and the trial form into one activity file. Same show name, choose **Add to**, drop it in, Run. The window runs from the first scan to 30 days after the last scan. Nadia's page shows the four piles with names and reasons. Check any booking matched by clinic.

## The run date

Normally leave **Run as of** alone. A generic thank-you more than three weeks after the show isn't drafted (Erin, Nadia, Nov 2); promises still are, with an apology for the delay. To rehearse an old show or see its first-week view, set the date to a few days after the show.

## If something goes wrong

- **Wrong match or next step:** press a decision, and write the fix on `rules.md` with the date and who decided.
- **"The run stopped":** nothing was sent. Keep the text it shows and send it to whoever looks after the tool (see the hand-off plan).
- **The page won't open:** another copy may still be running. Close its window and double-click again.
- **You're away:** it waits for you. Nobody else runs it unless Nadia decides otherwise.
- **Rehearsing:** practice runs add people to `memory.csv`. Use a separate copy of the folder.

## Mac: starting it

1. Unzip `Sprint3_handin.zip`, open `sandbar-sprint3`, double-click `start.command`. If the Mac blocks it: right-click, then Open.
2. If nothing opens, go to `http://localhost:8765` in a browser. Keep the small window open.
3. If Python is missing, install Python 3 from python.org.

## Friday demo

Before the call: unzip a fresh copy. Practice runs write to `memory.csv`, so don't use the folder you practised in. Close any older window so only one station is running.

1. Double-click `start.command`. Links can stay empty: drafts show a yellow marker.
2. Type the show's name. Drop all the files they hand over. Press Run.
3. If the show was over three weeks ago, thank-yous aren't drafted. To show the first-week view, open **Run as of** before pressing Run and pick a date a few days after the show.
4. **Erin** first: what came in, what she checks, what she hands to Owen and Nadia. Then **Owen**: promises on top, open a draft, Copy. Then **Nadia**: her drafts, Was this you?, the four piles.
5. Once the files are seen, change no code, rules or files.

To try it first without their files: use the three files in `toronto/`, Run as of `2026-09-17`. To see a finished run with nothing to start, open `sample_output_toronto/index.html`.

## For checking the tool (not part of Erin's job)

`python3 tests/run_all.py` runs every show, every attack and the page itself, and writes `reports/stress_test_report.html`, `stress_test_results.csv` and `critical_failures.csv`. Any test file in `tests/stress_cases/` also runs alone.
