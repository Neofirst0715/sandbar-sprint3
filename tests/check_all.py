#!/usr/bin/env python3
"""Runs every show through the same path the upload page uses (intake, rules, drafts, page) and scores it.
Right = appears once, right priority, right next step. Prints anyone who should get no email but has draft text."""
import csv, os, shutil, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import run as R
SHOWS = [("Toronto", "toronto", "answer_key/erin-recount-toronto.csv", "empty", "2026-09-17"),
         ("Toronto, reworded notes", "tests/data-reworded", "answer_key/erin-recount-toronto.csv", "empty", "2026-09-17"),
         ("Toronto, renamed columns", "tests/data-renamed", "answer_key/erin-recount-toronto.csv", "empty", "2026-09-17"),
         ("Moncton (hard made-up show)", "tests/blind_tests/moncton/show", "tests/blind_tests/moncton/answer_key.csv", "seed", None),
         ("Halifax (ordinary made-up show)", "tests/blind_tests/halifax/show", "tests/blind_tests/halifax/answer_key.csv", "seed", None)]
def srcs(p): return {x["id"] for x in p["records"]} | {n["source"] for n in p["notes"]}
fails = 0
for label, data, key, mem, today in SHOWS:
    out = tempfile.mkdtemp(); m = tempfile.mktemp(suffix=".csv")
    if mem == "seed": shutil.copy(os.path.join(ROOT, "memory.csv"), m)
    res, _ = R.run(os.path.join(ROOT, data), out, label.split(",")[0].split(" (")[0], today or "2027-06-01", m, None, day_one=True)
    keys = list(csv.DictReader(open(os.path.join(ROOT, key), encoding="utf-8-sig")))
    right = 0; wrong = []; leak = []
    rows = {id(r["p"]): r for r in res["drafts"]}
    for k in keys:
        want = {s.strip() for s in k["source_rows"].split(";") if s.strip()}
        main = {x for x in want if x[0] in "SC"} or want
        hits = [p for p in res["people"] if srcs(p) & main and p["real"]]
        if len(hits) == 1 and hits[0]["priority"] == k["priority"] and hits[0]["next_step"] == (k.get("promised_next_step") or k.get("next_step")): right += 1
        else: wrong.append(f"{k['name']}: want {k['priority']}/{k.get('promised_next_step') or k.get('next_step')}, got {[(p['name'], p['priority'], p['next_step']) for p in hits]}")
        if (k.get("email_ok") or "yes").lower().startswith("no"):
            for p in hits:
                if id(p) in rows and rows[id(p)]["body"]: leak.append(p["name"])
    print(f"{label}: {right} of {len(keys)}; no-email people with a draft: {leak or 'none'}")
    for w in wrong: print("   ", w)
    if leak: fails += 1
print("RED LINE FAILED" if fails else "Red line held on every show")
