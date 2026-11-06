#!/usr/bin/env python3
"""Runs everything and writes reports/stress_test_report.html, stress_test_results.csv and critical_failures.csv.
PASS and FAIL are measured. NEEDS REVIEW and NOT TESTED are never counted as passes."""
import csv, glob, html, importlib.util, json, os, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.request, uuid
from datetime import datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "tests", "stress_cases"), ROOT]
import _harness as H
for f in sorted(glob.glob(os.path.join(ROOT, "tests", "stress_cases", "test_*.py"))):
    spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
import run as R

# ---------- baselines ----------
def srcs(p): return {x["id"] for x in p["records"]} | {n["source"] for n in p["notes"]}
def baseline(cid, label, data, key, mem, today, need, tamper=False):
    def f():
        out = tempfile.mkdtemp(); m = tempfile.mktemp(suffix=".csv")
        if mem: shutil.copy(os.path.join(ROOT, "memory.csv"), m)
        res, _ = R.run(os.path.join(ROOT, data), out, label, today, m, None, day_one=True)
        keys = list(csv.DictReader(open(os.path.join(ROOT, key), encoding="utf-8-sig")))
        right = 0; wrong = []; leak = []
        rows = {id(r["p"]): r for r in res["drafts"]}
        for k in keys:
            want = {s.strip() for s in k["source_rows"].split(";") if s.strip()}; main = {x for x in want if x[0] in "SC"} or want
            hits = [p for p in res["people"] if srcs(p) & main and p["real"]]
            if len(hits) == 1 and hits[0]["priority"] == k["priority"] and hits[0]["next_step"] == k["promised_next_step"]: right += 1
            else: wrong.append(k["name"])
            if (k.get("email_ok") or "yes").lower().startswith("no"):
                leak += [p["name"] for p in hits if id(p) in rows and rows[id(p)]["body"]]
        return f"{right} of {len(keys)}; wrong: {wrong or 'none'}; must-not-email with a draft: {leak or 'none'}; privacy audit: {res.get('leaks') or 'clean'}", right >= need and not leak and not res.get("leaks")
    H.CASES.insert(0, dict(id=cid, title=label, section="Baseline", expected=f"At least {need} right; nobody who must not be emailed has a draft", critical=True, metric="baseline", fn=f))
TOR = "answer_key/erin-recount-toronto.csv"
baseline("BL5", "Halifax", "tests/blind_tests/halifax/show", "tests/blind_tests/halifax/answer_key.csv", True, "2027-06-01", 45)
baseline("BL4", "Moncton", "tests/blind_tests/moncton/show", "tests/blind_tests/moncton/answer_key.csv", True, "2027-06-01", 36)
baseline("BL3", "Toronto, renamed columns", "tests/data-renamed", TOR, False, "2026-09-17", 80)
baseline("BL2", "Toronto, reworded notes", "tests/data-reworded", TOR, False, "2026-09-17", 79)
baseline("BL1", "Toronto", "toronto", TOR, False, "2026-09-17", 80)
def script(cid, title, path, needle, expected):
    def f():
        r = subprocess.run([sys.executable, os.path.join(ROOT, path)], capture_output=True, text=True, timeout=280); last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
        return last[:200], needle in r.stdout and r.returncode == 0
    H.CASES.append(dict(id=cid, title=title, section="Baseline", expected=expected, critical=False, metric=None, fn=f))
script("BL6", "Moncton workbook, its own 15 cases", "tests/moncton_workbook_check.py", "14 of 15", "14 of 15 (the one left is Nadia's rule: a document request stays warm)")
script("BL7", "Every Toronto draft against Owen's and Nadia's rules", "tests/test_drafts.py", "all passed", "All pass")

# ---------- the page, through a real local server ----------
class Web:
    proc = None; port = None; dir = None
def web_start():
    Web.dir = tempfile.mkdtemp(); dst = os.path.join(Web.dir, "app"); shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("tests", "reports", "shows", "__pycache__", "sample_output_toronto", "docs"))
    s = socket.socket(); s.bind(("127.0.0.1", 0)); Web.port = s.getsockname()[1]; s.close()
    env = dict(os.environ, SANDBAR_PORT=str(Web.port), BROWSER="true"); Web.proc = subprocess.Popen([sys.executable, "server.py"], cwd=dst, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); Web.app = dst
    for _ in range(50):
        try:
            urlopen("/"); return
        except Exception: time.sleep(0.1)
def urlopen(path, data=None, headers=None):
    op = urllib.request.build_opener(urllib.request.ProxyHandler({})); return op.open(urllib.request.Request(f"http://localhost:{Web.port}{path}", data=data, headers=headers or {}), timeout=30)
def upload(show, files, mode="replace", today="2026-10-22"):
    b = uuid.uuid4().hex; body = b""
    for k, v in [("show", show), ("today", today), ("mode", mode)]: body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for n, t in files:
        data = t if isinstance(t, bytes) else t.encode()
        body += f'--{b}\r\nContent-Disposition: form-data; name="files"; filename="{n}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode() + data + b"\r\n"
    body += f"--{b}--\r\n".encode()
    r = urlopen("/run", body, {"Content-Type": "multipart/form-data; boundary=" + b}); return r.read().decode("utf8", "ignore"), r.geturl()
HDR = "first_name,last_name,company,email,share,notes\n"
def W(cid, title, expected, critical=False, metric=None):
    def deco(fn):
        H.CASES.append(dict(id=cid, title=title, section="Web", expected=expected, critical=critical, metric=metric, fn=fn)); return fn
    return deco
@W("W1", "Upload three Toronto files and press Run", "Page opens with Nadia, Owen and Erin", True, "crash")
def w1():
    files = [(n, open(os.path.join(ROOT, "toronto", n), "rb").read()) for n in ("badge-scans.csv", "booth-notes.json", "after-show-activity.csv")]
    page, url = upload("Toronto check", files, today="2026-09-17"); ok = all(f'data-v="{x}"' in page for x in ("nadia", "owen", "erin")); return f"{url.split('/shows/')[-1]}; buttons {ok}", ok
@W("W2", "Same show again, Replace (the default)", "Old file gone; old person not in the new run", True)
def w2():
    upload("Dup", [("a.csv", HDR + "Old,Person,Old Clinic,o@o.ca,Y,demo\n")]); page, _ = upload("Dup", [("b.csv", HDR + "New,Person,New Clinic,n@n.ca,Y,demo\n")]); return f"Old in page: {'Old Person' in page}; New in page: {'New Person' in page}", "Old Person" not in page and "New Person" in page
@W("W3", "Same show, Add to", "Both people in the run")
def w3():
    upload("Add", [("a.csv", HDR + "Old,Person,Old Clinic,o@o.ca,Y,demo\n")]); page, _ = upload("Add", [("b.csv", HDR + "New,Person,New Clinic,n@n.ca,Y,demo\n")], mode="add"); return f"Old: {'Old Person' in page}; New: {'New Person' in page}", "Old Person" in page and "New Person" in page
@W("W4", "Each run records its time and input files", "runs.jsonl has mode, time and files")
def w4():
    lines = open(os.path.join(Web.app, "shows", "dup", "runs.jsonl"), encoding="utf8").read().splitlines(); last = json.loads(lines[-1]); return str(last)[:150], len(lines) == 2 and last["mode"] == "replace" and last["files_in_run"] == ["b.csv"]
@W("W5", "Press a decision button", "Saved, show runs again, person leaves the to-do list")
def w5():
    upload("Dec", [("a.csv", "first_name,last_name,company,email,share,notes,scanned_by\nNia,Lane,Lane Clinic,n@l.ca,Y,talked about scheduling,Nadia\n")])
    r = urlopen("/decide", json.dumps(dict(show="dec", person="Nia Lane", clinic="Lane Clinic", decision="Owen", by="Nadia")).encode(), {"Content-Type": "application/json"}); page = urlopen("/shows/dec/out/index.html").read().decode("utf8")
    saved = open(os.path.join(Web.app, "shows", "dec", "out", "decisions.csv"), encoding="utf8").read(); return f"{r.status}; saved {'Nia Lane' in saved}; still asking: {'Was this you? (1)' in page}", r.status == 200 and "Nia Lane" in saved and "Was this you? (1)" not in page
@W("W6", "Nothing typed releases an N flag, through the server", "Still held", True, "consent")
def w6():
    upload("Nf", [("a.csv", HDR + "Nia,Lane,Lane Clinic,n@l.ca,N,wants a demo\n")]); urlopen("/decide", json.dumps(dict(show="nf", person="Nia Lane", clinic="Lane Clinic", decision="OK", by="Erin")).encode(), {"Content-Type": "application/json"})
    rows = list(csv.DictReader(open(os.path.join(Web.app, "shows", "nf", "out", "drafts.csv"), encoding="utf8"))); return f"{rows[0]['status'][:40]} body='{rows[0]['body']}'", rows[0]["status"].startswith("HOLD") and not rows[0]["body"]
@W("W7", "Reading files outside the shows folder", "Refused", True)
def w7():
    import http.client
    c = http.client.HTTPConnection("localhost", Web.port); c.request("GET", "/shows/../memory.csv"); s1 = c.getresponse().status; return f"memory.csv -> {s1}", s1 == 404
@W("W8", "A made-up decision value", "Refused")
def w8():
    try: urlopen("/decide", json.dumps(dict(show="dec", person="x", clinic="y", decision="Release", by="Erin")).encode(), {"Content-Type": "application/json"}); return "accepted", False
    except urllib.error.HTTPError as e: return f"{e.code}", e.code == 400
@W("W9", "Only broken files dropped", "Plain message, the station keeps running", True, "crash")
def w9():
    page, _ = upload("Bad", [("x.json", "{bad")]); alive = urlopen("/").status; return f"message shown: {'The run stopped' in page}; still up: {alive}", "The run stopped" in page and alive == 200
@W("W10", "A page with one bad date among good rows", "Runs; problem shown on Erin's page", True, "crash")
def w10():
    page, _ = upload("Bd", [("a.csv", HDR + "Nia,Lane,Lane Clinic,n@l.ca,Y,wants a demo\n"), ("b.csv", "event_id,date_time,event,channel,name,email,clinic,detail\nE1,banana,demo booked,x,Nia Lane,n@l.ca,Lane Clinic,\n")]); return f"Under Check with the bad value: {'Check (' in page and 'banana' in page}", "Check (" in page and "banana" in page
@W("W11", "Page in a real browser: three buttons switch views", "Each view appears when pressed; no script errors")
def w11():
    try: from playwright.sync_api import sync_playwright
    except Exception: return dict(status="NOT TESTED", actual="Python Playwright isn't installed here")
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(); p = b.new_page(); errs = []; p.on("pageerror", lambda e: errs.append(str(e))); p.goto(f"http://localhost:{Web.port}/shows/toronto-check/out/index.html"); seen = []
            for w in ("Nadia", "Owen", "Erin"):
                p.click(f'nav button:has-text("{w}")'); seen.append(p.inner_text("section.on .lead")[:30])
            b.close(); return f"{seen}; errors {errs}", len(set(seen)) == 3 and not errs
    except Exception as ex: return dict(status="NOT TESTED", actual=f"Browser wouldn't start here: {str(ex)[:80]}")

# ---------- things that can't be measured here ----------
for cid, title, why, sect in [("NT1", "Double-clicking start.command on a Mac", "Run on Neo's Mac before the demo; the tests run on Linux", "Web"), ("NT2", "start.bat on Windows", "No Windows machine available", "Web"), ("NT3", "The page on a real phone (Copy, Open in my mail)", "Checked at phone width in a desktop browser only", "Web"), ("NT4", "The Sheet opened in Google Sheets", "Only written and read back as a file here", "Input"), ("NT5", "Dragging files onto the box", "Tests upload through the form, not a real drag", "Web"), ("NT6", "Whether Owen would send these drafts", "Owen hasn't read them", "Attack A-V")]:
    H.CASES.append(dict(id=cid, title=title, section=sect, expected="A person tries it", critical=False, metric=None, fn=lambda why=why: dict(status="NOT TESTED", actual=why)))
for cid, title, why, sect in [("R-1", "Holding Amira and other N-flag people who asked at the booth", "Follows Erin's and Nadia's 'hold N' rule, but Erin also said Amira gets a plain reply. Nadia or someone who knows the law should confirm", "Consent"), ("R-2", "Counting bookings made during the show", "Counted, as it fits 'booked by day 30 counts'. The written request says only after the show. Nadia should confirm", "Day 30"), ("R-3", "Same name, different clinic waits for Erin", "Safe, but it holds some real people until she checks", "Attack A-V")]:
    H.CASES.append(dict(id=cid, title=title, section=sect, expected="A person decides", critical=False, metric=None, fn=lambda why=why: dict(status="NEEDS REVIEW", actual=why)))

METRICS = [("baseline", "Baselines at or above target", "all pass"), ("unsubscribe", "Historical unsubscribe draft leakage", "0"), ("consent", "Unauthorized marketing draft", "0"), ("privacy", "Sensitive private information leakage", "0"), ("preshow", "Pre-show event misclassification", "0"), ("window", "Out-of-window Day-30 events", "0"), ("duplicate", "Duplicate event counting", "0"), ("invalidemail", "Invalid email draft", "0"), ("crossperson", "Cross-person information leakage", "0"), ("crash", "Crash on malformed input", "0")]

PRE = "see KNOWN_ISSUES.md"
if os.path.exists(os.path.join(ROOT, "reports", "pre_fix_summary.txt")): PRE = open(os.path.join(ROOT, "reports", "pre_fix_summary.txt"), encoding="utf8").read().strip()
def main():
    web_start()
    try: results = H.run_cases()
    finally:
        if Web.proc: Web.proc.terminate()
    rep = os.path.join(ROOT, "reports"); os.makedirs(rep, exist_ok=True)
    fields = ["id", "section", "title", "status", "critical", "expected", "actual"]
    with open(os.path.join(rep, "stress_test_results.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields, extrasaction="ignore"); w.writeheader(); w.writerows(results)
    crit = [r for r in results if r["critical"] and r["status"] == "FAIL"]
    with open(os.path.join(rep, "critical_failures.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields, extrasaction="ignore"); w.writeheader(); w.writerows(crit)
    count = lambda rs, st: sum(1 for r in rs if r["status"] == st)
    e = lambda s: html.escape(str(s))
    tile = "".join(f"<div class='t {s.split()[0].lower()}'><b>{count(results, s)}</b>{s}</div>" for s in ("PASS", "FAIL", "NEEDS REVIEW", "NOT TESTED"))
    metric_rows = ""
    for key, label, need in METRICS:
        ms = [r for r in results if r["metric"] == key]; bad = count(ms, "FAIL")
        metric_rows += f"<tr><td>{e(label)}</td><td>{need}</td><td>{'all pass' if key == 'baseline' and not bad else bad} ({len(ms)} checks)</td><td class='{'fail' if bad else 'pass'}'>{'FAIL' if bad else 'PASS'}</td></tr>"
    sections = ""
    for sec in H.SECTIONS:
        rs = [r for r in results if r["section"] == sec]
        sections += f"<h2>{e(sec)} <small>{count(rs,'PASS')} pass, {count(rs,'FAIL')} fail, {count(rs,'NEEDS REVIEW')} review, {count(rs,'NOT TESTED')} not tested</small></h2><div class='wrap'><table><tr><th>ID</th><th>Test</th><th>Expected</th><th>Actual</th><th>Result</th></tr>"
        for r in rs:
            sections += f"<tr><td>{e(r['id'])}</td><td>{e(r['title'])}</td><td>{e(r['expected'])}</td><td class='a'>{e(r['actual'])}</td><td class='{r['status'].split()[0].lower()}'>{e(r['status'])}</td></tr>"
        sections += "</table></div>"
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sandbar stress test report</title><style>
body{{font:15px/1.45 -apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:#1d2326;background:#f7f6f2;margin:0 auto;padding:16px;max-width:1100px}}h1{{font-size:24px;margin:8px 0}}h2{{font-size:17px;margin:26px 0 8px}}h2 small{{font-weight:400;color:#6b7378;font-size:13px}}
.ts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin:12px 0}}.t{{background:#fff;border:1px solid #e3e1db;border-radius:10px;padding:10px;text-align:center;font-size:13px}}.t b{{display:block;font-size:28px}}
.wrap{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;background:#fff;font-size:13px}}th,td{{border:1px solid #e3e1db;padding:6px 8px;text-align:left;vertical-align:top}}th{{background:#efede8}}td.a{{overflow-wrap:anywhere;max-width:380px}}.pass{{color:#1f7a4a;font-weight:700}}.fail{{color:#b3261e;font-weight:700}}.needs,.not{{color:#8a6100;font-weight:700}}p{{color:#4a5257}}</style></head><body>
<h1>Sandbar stress test report</h1><p>Run {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC on Linux, by <code>python3 tests/run_all.py</code>. I wrote these tests after seeing the failures, so they guard against repeats. They are not a blind test. The same A-V checks on the code before these fixes: {PRE}. NEEDS REVIEW and NOT TESTED are not counted as passes.</p>
<div class="ts">{tile}</div><h2>Acceptance</h2><div class="wrap"><table><tr><th>Measure</th><th>Required</th><th>Actual</th><th>Result</th></tr>{metric_rows}</table></div>{sections}</body></html>"""
    with open(os.path.join(rep, "stress_test_report.html"), "w", encoding="utf-8") as f: f.write(page)
    print(f"PASS {count(results,'PASS')}  FAIL {count(results,'FAIL')}  NEEDS REVIEW {count(results,'NEEDS REVIEW')}  NOT TESTED {count(results,'NOT TESTED')}  critical failures {len(crit)}")
    for r in results:
        if r["status"] == "FAIL": print(f"FAIL {r['id']} {r['title']}\n   expected: {r['expected']}\n   actual: {r['actual'][:400]}")
    return 1 if count(results, "FAIL") else 0
if __name__ == "__main__": sys.exit(main())
