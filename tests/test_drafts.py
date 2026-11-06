"""Owen's four reasons to ignore a draft, Nadia's red lines, and the rules from the interviews, checked on every draft."""
import os, re, sys, tempfile, shutil, csv
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sandbar
HERE = os.path.dirname(os.path.abspath(__file__)); SHOW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "toronto")
day1 = sandbar.run(SHOW, tempfile.mkdtemp(), before_followup=True)
rows = day1["drafts"]; real = [r for r in rows if r["body"]]; bad = []
def check(name, failures):
    print(("PASS " if not failures else "FAIL ") + f"{name}" + (f": {failures[:6]}" if failures else "")); bad.extend(failures)
check("one row per real conversation", [] if len(rows) == len(day1["real"]) else ["count"])
check("nobody appears twice", [r["name"] for r in rows if sum(1 for x in rows if x["to"] and x["to"] == r["to"]) > 1])
hold = [r for r in rows if r["p"]["hold"]]
check("held people have no draft", [r["name"] for r in hold if r["body"]])
drive = [p["name"] for p in day1["people"] if not p["real"]]
check("drive-bys, vendors, students have no draft", [r["name"] for r in rows if r["name"] in drive])
check("personal details", [r["name"] for r in real if re.search(r"\b(dad|father|hospital|dog|photos|hockey|kids|bow tie|Dal|knew Sam|retir)\b", r["body"], re.I)])
check("robot phrases", [r["name"] for r in real if re.search(r"hope this email|pleasure connecting|reach out|touch base|valued|features include|great to meet", r["body"], re.I)])
check("wrong link: call backs have none", [r["name"] for r in real if r["next_step"] == "call back" and re.search(r"\[|http", r["body"])])
check("wrong link: thank-yous have none", [r["name"] for r in real if r["next_step"] == "thank-you note" and re.search(r"\[|http", r["body"])])
check("wrong link: 'maybe next year' has no demo link", [r["name"] for r in real if re.search(r"maybe next y", " ".join(x["text"] for x in r["p"]["records"]) + r["p"]["booth_detail"], re.I) and "DEMO" in r["body"]])
check("demo asks get the booking link", [r["name"] for r in real if r["next_step"] == "demo" and "DEMO" not in r["body"] and r["language"] == "English"])
check("pricing has the number typed in", [r["name"] for r in real if r["next_step"] == "pricing" and "34" not in r["body"]])
check("trial has the line about getting stuck", [r["name"] for r in real if r["next_step"] == "trial" and "stuck" not in r["body"]])
check("three or four lines (at most 6 sentences)", [r["name"] for r in real if len(re.findall(r"[.?!](\s|$)", r["body"])) > 6])
check("signed by the sender", [r["name"] for r in real if not r["body"].endswith(r["sender"] + ".")])
check("specific detail or flagged for the sender", [r["name"] for r in real if "You " not in r["body"] and "vous" not in r["body"].lower() and r["next_step"] not in ("call back",) and "add the one thing" not in r["check"] and "add one thing" not in r["check"] and "to pass along" not in r["body"]])
print("sentences per draft, max:", max(len(re.findall(r"[.?!](\s|$)", r["body"])) for r in real), "| drafts:", len(real), "| held:", len(hold), "| no detail, flagged:", sum("add the one thing" in r["check"] for r in real))
if os.path.basename(os.path.normpath(SHOW)) == "toronto":
    want = "Kevin, good to meet you in Toronto. You mentioned you're running things in Excel, so if that ever starts getting messy, give me a shout. Owen."
    check("Owen's Kevin example, word for word", [] if next(r["body"] for r in rows if r["name"].startswith("Kevin")) == want else ["kevin"])
    # second run: already written to means nothing new goes out
    later = sandbar.run(SHOW, tempfile.mkdtemp())
    check("second run never re-offers someone already written to", [r["name"] for r in later["drafts"] if r["p"].get("sent") and not (r["status"].startswith("ALREADY") or r["status"].startswith(("NO DRAFT","HOLD")))])
    print("second run statuses:", sorted({r["status"].split(":")[0].split("(")[0].strip() for r in later["drafts"]}))
print("RESULT:", "all passed" if not bad else f"{len(bad)} failures")
