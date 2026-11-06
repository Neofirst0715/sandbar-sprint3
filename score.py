#!/usr/bin/env python3
"""Compare the tool with Erin's recount. Holdout people are never printed unless --holdout."""
import argparse, csv, random, sys
from collections import Counter
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import sandbar

KEY = __file__.rsplit("/", 1)[0] + "/answer_key/erin-recount-toronto.csv"
def holdout_ids(rows):
    rnd = random.Random(20261103); ids = []
    for pr, n in [("hot", 4), ("warm", 8), ("cold", 8)]:
        pool = sorted(r["person_id"] for r in rows if r["priority"] == pr)
        ids += rnd.sample(pool, n)
    return set(ids)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("show"); ap.add_argument("out"); ap.add_argument("--holdout", action="store_true"); ap.add_argument("--state", default=None)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(KEY, encoding="utf-8-sig")))
    hold = holdout_ids(rows)
    r = sandbar.run(a.show, a.out, a.state)
    def srcs(p): return {x["id"] for x in p["records"]} | {n["source"] for n in p["notes"]}
    keysrc = set()
    results = []; consent_err = []
    for k in rows:
        want = {s.strip() for s in k["source_rows"].split(";")}; keysrc |= want
        main_rows = {x for x in want if x[0] in "SC"} or want
        hits = [p for p in r["people"] if srcs(p) & main_rows]
        real_hits = [p for p in hits if p["real"]]
        errs = []
        if len(real_hits) != 1: errs.append(f"appears {len(real_hits)} times")
        else:
            p = real_hits[0]
            if srcs(p) != want: errs.append(f"sources differ: missing {sorted(want-srcs(p))} extra {sorted(srcs(p)-want)}")
            if p["priority"] != k["priority"]: errs.append(f"priority {p['priority']} vs {k['priority']}")
            if p["next_step"] != k["promised_next_step"]: errs.append(f"next step {p['next_step']} vs {k['promised_next_step']}")
        if len(real_hits) == 1 and real_hits[0]["contact_source"] != k["consent"] and not (k["consent"].startswith("badge") and real_hits[0]["contact_source"].startswith("badge")):
            consent_err.append((k["name"], real_hits[0]["contact_source"], k["consent"]))
        pile = {"demo": "booked a demo", "trial": "started a trial", "no reply": "written to, nothing came of it", "never followed up": "never written to"}[k["day30_result"]]
        pile_err = ""
        if len(real_hits) == 1 and real_hits[0].get("pile") != pile: pile_err = f"pile {real_hits[0].get('pile')} vs {pile}"
        results.append(dict(id=k["person_id"], name=k["name"], errs=errs, pile_err=pile_err, held=k["person_id"] in hold, key=k, hit=real_hits[0] if len(real_hits)==1 else None))
    dev = [x for x in results if not x["held"]]; test = [x for x in results if x["held"]]
    print(f"Tuning set: {sum(not x['errs'] for x in dev)} of {len(dev)} fully right")
    for x in dev:
        if x["errs"]: print("  ", x["id"], x["name"], "->", "; ".join(x["errs"]))
    if a.holdout:
        print(f"HELD-OUT: {sum(not x['errs'] for x in test)} of {len(test)} fully right")
        for x in test:
            if x["errs"]: print("  ", x["id"], x["name"], "->", "; ".join(x["errs"]))
    else:
        print(f"Held-out: {len(test)} people not looked at")
    extra = [p for p in r["real"] if not (srcs(p) & keysrc)]
    print("Real in tool, not in recount:", [(p["name"], p["real_why"], sorted(srcs(p))) for p in extra])
    pool = dev if not a.holdout else results
    print("Contact source differs from recount:", consent_err)
    print("Piles:", dict(Counter(p.get("pile") for p in r["real"])), "| pile errors:", [(x["name"], x["pile_err"]) for x in pool if x["pile_err"]])
    print("Priority counts:", dict(Counter(p["priority"] for p in r["real"])), "Next:", dict(Counter(p["next_step"] for p in r["real"])))
    print("Flags per person:", sum(len(p["flags"]) for p in r["real"]), "on", sum(1 for p in r["real"] if p["flags"]), "people; general", [(g["source"], g["reason"]) for g in r["general"]])
    print("Flag owners:", dict(Counter((f.split(":")[0] if f.startswith("For ") else "Erin/Owen other") for p in r["real"] for f in p["flags"])))
    print("French:", [p["name"] for p in r["real"] if p["french"]], "First batch:", sum(p["first_batch"] for p in r["real"]))
    print("Held (no draft):", [p["name"] for p in r["real"] if p["hold"]])
    print("Warnings:", [w for w in r["warnings"] if not w.startswith("COLUMN")])
main()
