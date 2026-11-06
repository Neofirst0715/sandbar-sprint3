# Sandbar after-show station

Volta Anchor · Sprint 3 · *Find out why booth conversations go cold, then fix it* · Zhenzhao (Neo) Li

After a trade show, Sandbar's booth conversations sit in four places and nobody owns the week after. This tool reads the scan export, cards, voice notes and Owen's list, finds each real conversation once, decides priority, next step and who sends, writes a short draft, flags what it can't decide, and at day 30 sorts everyone into Nadia's four piles. One page, three buttons: Nadia, Owen, Erin. Each email goes from whoever had the conversation, from their own mailbox. Erin checks and coordinates; she doesn't send. **Nothing is sent, no AI service is used, and nothing leaves the computer.**

## Run it

Double-click `start.command` (Mac; the first time, right-click, then Open) or `start.bat` (Windows). The upload page opens at `http://localhost:8765`. Name the show, drop every file from the show into the box, press Run. Steps for Erin: `HOW-TO-RUN.md`. Rules with dates: `rules.md`.

No browser? `python3 run.py --data toronto --out out --show Toronto --today 2026-09-17`, then open `out/index.html`.

## Results

Right = appears once, with the right priority and the right next step. Re-run everything with `python3 tests/run_all.py`. Results land in `reports/`.

| Show | Result | How much to trust it |
|---|---|---|
| Toronto, against Erin's recount | 80 of 80 | Best case: the rules came from the same material |
| Toronto, reworded notes | 79 of 80 | After adding the words it first missed. The last one's new wording no longer says what was asked |
| Toronto, other column names | 80 of 80 | |
| Moncton (hard, made up by someone who hadn't seen the tool) | First run 20 of 37; now 36 of 37 | Only the 20 was blind |
| Halifax (ordinary, made up the same way) | First run 43 of 45; now 45 of 45 | Only the 43 was blind |
| Moncton workbook, its own 15 cases | 14 of 15 | The one left is a rule difference: Nadia ruled a document request stays warm |
| Attack tests, A to V, plus broken files and the page | 202 pass, 0 fail, 3 need a person's decision, 6 not tested | Written after seeing the failures, so not blind. The same A to V checks failed 123 of 175 on the code before the fixes |

Full results: `reports/stress_test_report.html`. What's still open: `KNOWN_ISSUES.md`.

## Files

- `server.py`, `start.command`, `start.bat`: the upload page.
- `run.py`: one run. `intake.py` recognises each file or Excel sheet by its header. `privacy.py` keeps personal remarks out. `sandbar.py` finds people and applies the rules. `drafts.py` writes drafts. `memory.py` remembers earlier shows in `memory.csv`. `decisions.py` keeps what people decided. `page.py` makes the three-button page. `sheet.py` makes the same thing as a Sheet.
- `shows/<show>/out/`: created by each run. `index.html`, `Sandbar_follow_up.xlsx`, `drafts.csv`, `flags.csv`, `piles.csv`, `people.csv`, `not_a_conversation.csv`, `input_issues.csv`, `day30_page.html`.
- `toronto/`, `answer_key/`: the Toronto files and Erin's recount. `tests/`: the checks and test shows. `tests/stress_cases/`: the attacks, one file per type, each building its own small show. `reports/`: the latest results.
- `docs/`: the problem, the hand-off plan, the four-risk research and the interview transcripts.

The data is simulated and comes from the Volta Anchor interviews.
