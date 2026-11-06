"""Shared tools for the attack tests. Every test builds its own small show in a temp folder.
No test reads or changes Toronto, Moncton or Halifax, and none touches the real memory.csv."""
import csv, glob, json, os, re, sys, tempfile, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import run as R, sandbar, drafts, privacy, intake
HEAD = "scan_id,scanned_at,scanned_by,first_name,last_name,title,company,email,phone,city,province,share_with_exhibitors,rating,notes".split(",")
SECTIONS = ["Baseline", "Attack A-V", "Privacy", "Consent", "Day 30", "Web", "Input"]
CASES = []

def case(cid, title, section, expected, critical=False, metric=None):
    """Decorator: the function returns (actual text, passed)."""
    def wrap(fn):
        CASES.append(dict(id=cid, title=title, section=section, expected=expected, critical=critical, metric=metric, fn=fn)); return fn
    return wrap

def scan(i, f, l, co, em, share="Y", note="talked about scheduling", rating="", at="2026-10-20 10:00", phone="", by="Owen"):
    return dict(scan_id=i, scanned_at=at, scanned_by=by, first_name=f, last_name=l, title="", company=co, email=em, phone=phone, city="", province="", share_with_exhibitors=share, rating=rating, notes=note)
def card(i, n, co, em, back, by="Owen", phone="", typed="2026-10-21"):
    return dict(card_id=i, name=n, title="", clinic=co, email=em, phone=phone, back_of_card=back, collected_by=by, typed_on=typed)
def ev(i, when, e, name="", em="", co="", det="", ch="hello"):
    return dict(event_id=i, date_time=when, event=e, channel=ch, name=name, email=em, clinic=co, detail=det)
def dne(n, em, co): return dict(name=n, email=em, clinic=co, show="Old Show 2026", status="do not email", date="2026-01-15", note="asked to be removed")
TWO_DAYS = [scan("S90", "Zed", "Filler", "Filler Clinic", "zed@filler.ca", note="chat", at="2026-10-20 09:00"), scan("S91", "Zoe", "Filler", "Other Filler", "zoe@otherfiller.ca", note="chat", at="2026-10-21 17:00")]

def show(scans=(), cards=(), voice=(), lines=(), activity=(), mem=(), today="2026-10-22", raw=None, decisions=(), settings=None, memfile=None, name="Test Show"):
    d = tempfile.mkdtemp(); out = tempfile.mkdtemp(); m = memfile or tempfile.mktemp(suffix=".csv")
    if scans:
        with open(d + "/badge-scans.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, HEAD); w.writeheader(); w.writerows(scans)
    json.dump(dict(about="Typed up from the Test booth (Testville, )", cards=list(cards), voice_notes=[dict(note_id=f"V{i}", transcript=t, recorded_at=a) for i, (t, a) in enumerate(voice)],
                   owen_list=dict(lines=[dict(line_id=f"L{i}", text=t) for i, t in enumerate(lines)])), open(d + "/booth-notes.json", "w", encoding="utf-8"), ensure_ascii=False)
    if activity:
        with open(d + "/after-show-activity.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, "event_id date_time event channel name email clinic detail".split()); w.writeheader(); w.writerows(activity)
    if not memfile:
        with open(m, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, "name email clinic show status date note".split()); w.writeheader(); w.writerows(mem)
    if decisions:
        with open(out + "/decisions.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, "person clinic decision by date".split()); w.writeheader(); w.writerows(decisions)
    if raw: raw(d)
    st = None
    if settings:
        st = tempfile.mktemp(suffix=".json"); json.dump(settings, open(st, "w"))
    res, got = R.run(d, out, name, today, m, st)
    return dict(res=res, got=got, out=out, memory=m, data=d)

def row(s, name):
    for r in s["res"]["drafts"]:
        if name in r["name"]: return r
    return None
def person(s, name):
    return next((p for p in s["res"]["people"] if name in p["name"]), None)
def short(r):
    if not r: return "no row (not a real conversation)"
    return f"status='{r['status'][:60]}' draft={'yes' if r['body'] else 'no'} step={r['next_step']} from={r['sender']} lang={r['language']} to='{r['to']}'"
def no_draft(s, name):
    r = row(s, name); return (short(r), r is None or not r["body"])
def issues(s): return s["res"].get("issues", []) + s["got"].get("issues", [])
def files_text(folder):
    """Every written file as text, Sheet included."""
    out = {}
    for path in glob.glob(folder + "/**/*", recursive=True):
        if not os.path.isfile(path): continue
        if path.endswith(".xlsx"):
            z = zipfile.ZipFile(path); out[os.path.relpath(path, folder)] = " ".join(z.read(n).decode("utf8", "ignore") for n in z.namelist())
        elif path.endswith((".csv", ".html", ".txt", ".json")):
            out[os.path.relpath(path, folder)] = open(path, encoding="utf8", errors="ignore").read()
    return out
def leaks(s, pattern):
    """Which written files contain this pattern as a whole word."""
    return sorted(f for f, t in files_text(s["out"]).items() if re.search(pattern, t, re.I))

def run_cases(cases=None):
    results = []
    for c in (cases if cases is not None else CASES):
        rec = {k: c[k] for k in ("id", "title", "section", "expected", "critical", "metric")}
        try:
            got = c["fn"]()
            if isinstance(got, dict):
                rec["status"], rec["actual"] = got["status"], got["actual"]
            else:
                actual, ok = got
                rec["actual"], rec["status"] = str(actual), "PASS" if ok else "FAIL"
        except Exception as ex:
            rec["status"], rec["actual"] = "FAIL", f"CRASH: {ex!r}"
        results.append(rec)
    return results
def main():
    for r in run_cases():
        print(f"{r['status']:5} {r['id']:6} {r['title']}\n      expected: {r['expected']}\n      actual:   {r['actual']}")
