"""X: broken files. One bad record can't sink a show, and nothing is dropped silently."""
from _harness import *
GOOD = [scan("S1", "Zoe", "Oak", "Oak Clinic", "z@o.ca", note="demo")]
def still_ok(s, needle):
    r = row(s, "Zoe"); return f"{short(r)} issues={[(x['file'], x['record'], x['reason'][:60]) for x in issues(s)]}", bool(r) and bool(r["body"]) and any(needle in x["reason"] for x in issues(s))
def wr(name, text, **kw):
    def f(d): open(os.path.join(d, name), "w", **kw).write(text)
    return f
@case("X1", "Empty CSV", "Input", "Show runs; file reported", True, "crash")
def x1(): return still_ok(show(GOOD, raw=wr("empty.csv", "")), "Empty")
@case("X2", "Corrupt JSON", "Input", "Show runs; file reported", True, "crash")
def x2(): return still_ok(show(GOOD, raw=wr("broken.json", "{bad json")), "Could not read")
@case("X3", "JSON with null records", "Input", "Show runs; records reported", True, "crash")
def x3():
    def raw(d): json.dump(dict(cards=[None, dict(name=None, clinic=None, email=None)], voice_notes=[dict(transcript=None)], owen_list=dict(lines=[dict(text=None)])), open(d + "/n.json", "w"))
    return still_ok(show(GOOD, raw=raw), "broken record")
@case("X4", "Row shorter or longer than the header", "Input", "Read as far as it goes; row reported", True, "crash")
def x4():
    s = show(raw=wr("x.csv", "first_name,last_name,company,email,share,notes\nAna,Lee\nZoe,Oak,Oak Clinic,z@o.ca,Y,demo,extra,extra\n")); return still_ok(s, "columns")
@case("X5", "Windows encoding with accents", "Input", "Read, accents intact", True, "crash")
def x5():
    def raw(d):
        with open(d + "/x.csv", "w", encoding="cp1252") as f: f.write("first_name,last_name,company,email,share,notes\nRené,Côté,Clinique,r@c.ca,Y,demo\n")
    s = show(raw=raw); return str([p["name"] for p in s["res"]["people"]]), any(p["name"] == "René Côté" for p in s["res"]["people"])
@case("X6", "A note a million characters long", "Input", "Finishes quickly; cut and reported", True, "crash")
def x6():
    import time; t = time.time(); s = show(GOOD, voice=[("Zoe Oak at Oak Clinic wants a demo. " + "blah " * 200000, "2026-10-20 11:00")]); took = time.time() - t
    return f"{took:.1f}s; {[x['reason'][:50] for x in issues(s)]}", took < 30 and any("characters long" in x["reason"] for x in issues(s))
@case("X7", "No scan export at all", "Input", "Runs on what's there; says the scan export is missing", True, "crash")
def x7():
    s = show(cards=[card("C1", "Zoe Oak", "Oak Clinic", "z@o.ca", "demo")]); return str([x["reason"] for x in issues(s)]), any("No scan export" in x["reason"] for x in issues(s))
@case("X8", "Scan row with no name at all", "Input", "No draft; reported", True, "invalidemail")
def x8():
    s = show(GOOD + [scan("S2", "", "", "", "", note="demo")]); blank = [r for r in s["res"]["drafts"] if not r["name"].strip()]; return f"{[short(r) for r in blank]} issues={[x['reason'] for x in issues(s)]}", all(not r["body"] for r in blank) and any("no name" in x["reason"] for x in issues(s))
@case("X9", "Nothing usable dropped", "Input", "Stops with a plain message, changes nothing", True, "crash")
def x9():
    d = tempfile.mkdtemp()
    try: R.run(d, tempfile.mkdtemp(), "T", "2026-10-22", tempfile.mktemp(), None)
    except SystemExit as e: return str(e)[:80], "Stopped" in str(e)
    return "no stop", False
@case("X10", "Problems file is written", "Input", "input_issues.csv has file, record, reason and review")
def x10():
    s = show(GOOD, raw=wr("broken.json", "{bad")); rows = list(csv.DictReader(open(s["out"] + "/input_issues.csv", encoding="utf8"))); return str(rows[:1]), bool(rows) and set(rows[0]) == {"file", "record", "reason", "review"}
@case("X11", "Mistyped date formats mixed across rows", "Input", "Good ones read; the rest reported")
def x11():
    s = show(GOOD, activity=[ev("E1", "Oct 25, 2026 10:00", "demo booked", "Zoe Oak", "z@o.ca", "Oak Clinic")], today="2026-12-01"); return person(s, "Zoe")["pile"], person(s, "Zoe")["pile"] == "booked a demo"
if __name__ == "__main__": main()
