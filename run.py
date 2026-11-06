#!/usr/bin/env python3
"""One run: tidy the dropped files, apply the rules, write the drafts, the Sheet and the three-button page.
Nothing is sent. No AI. No outside server. Standard library only.

    python3 run.py --data toronto --out out --show Toronto [--today 2026-09-17] [--memory memory.csv] [--settings settings.json]
"""
import argparse, json, os, shutil, sys, tempfile
from datetime import date, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import intake, page, privacy, sandbar

def run(data, out, show, today=None, memory=None, settings=None, day_one=False):
    st = {}
    if settings and os.path.exists(settings):
        st = {k: v for k, v in json.load(open(settings, encoding="utf-8")).items() if v}
    os.makedirs(out, exist_ok=True)
    tidy = tempfile.mkdtemp(prefix="sandbar_")  # raw notes never sit among the results
    old = os.path.join(out, "_input")
    if os.path.isdir(old): shutil.rmtree(old)
    try:
        got = intake.prepare(data, tidy, show, st)
        when = datetime.strptime(today, "%Y-%m-%d") if today else datetime.now()
        res = sandbar.run(tidy, out, state=memory, before_followup=day_one, today=when)
    finally:
        shutil.rmtree(tidy, ignore_errors=True)
    # everything found wrong with the files, in one place
    sandbar.write_issues(out, got["issues"] + res["issues"])
    # last look: the notes' own personal clauses must not be in anything written
    leaks = privacy.audit_outputs(out, res["raw_private"])
    for f, c in leaks.items():
        res["warnings"].append(f"Stop: privacy check found a personal remark in {f}. Don't share this run. Keep this message for whoever looks after the tool.")
    page.render(res, got, show, when, os.path.join(out, "index.html"), memory_path=memory)
    leaks = privacy.audit_outputs(out, res["raw_private"])
    res["leaks"] = leaks
    return res, got

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); ap.add_argument("--show", default="the show")
    ap.add_argument("--today", default=date.today().isoformat()); ap.add_argument("--memory", default=os.path.join(HERE, "memory.csv"))
    ap.add_argument("--settings", default=os.path.join(HERE, "settings.json")); ap.add_argument("--day-one", action="store_true", help="draft as on day 1, ignoring what was already sent")
    a = ap.parse_args()
    res, got = run(a.data, a.out, a.show, a.today, a.memory, a.settings, a.day_one)
    print(f"{len(res['real'])} real conversations of {len(res['people'])} people. Open {os.path.join(a.out, 'index.html')}")
    for w in res["warnings"]:
        if not w.startswith("COLUMN CHECK"): print("WARNING:", w)
    for w in got["ignored"]: print("IGNORED:", w)
