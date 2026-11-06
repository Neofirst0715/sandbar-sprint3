#!/usr/bin/env python3
"""The 15 cases in the Moncton workbook's own matrix, run from the one Excel file through the upload path.
One is expected to differ: M_S13 (Nathan) says hot, but Nadia ruled on Nov 4 that a document request stays warm."""
import os, shutil, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
import run as R
m = tempfile.mktemp(suffix=".csv"); shutil.copy(os.path.join(ROOT, "memory.csv"), m)
res, _ = R.run(os.path.join(ROOT, "tests/moncton_workbook"), tempfile.mkdtemp(), "Moncton", "2026-10-24", m, None)
P = {p["last"]+p["first"][:2].lower(): p for p in res["people"]}; D = {id(r["p"]): r for r in res["drafts"]}
def get(n): return next(p for p in res["people"] if n in p["name"])
def body(n): r = D.get(id(get(n))); return r["body"] if r else ""
def status(n): r = D.get(id(get(n))); return r["status"] if r else "not a conversation"
c = [("M_S01 Marcus: pre-show booking not in demo pile", get("Vance")["pile"] != "booked a demo" and not body("Vance")),
     ("M_S02 Jen: no second intro", not body("MacIsaac")), ("M_S03 Arthur: no draft", not body("Pendleton")),
     ("M_S04 Sylvie: N flag with card, no draft", not body("Boucher") and "Share flag N" in status("Boucher")), ("M_S05 Kyle: drive-by, no draft", not get("Brody")["real"]),
     ("M_S06 Claire: nothing personal", "divorce" not in body("Dunphy").lower() and "husband" not in body("Dunphy").lower() and body("Dunphy")),
     ("M_S07 Tariq: pricing, no demo link", "$34" in body("Mansoor") and "[DEMO" not in body("Mansoor")), ("M_S08 Jean: one person, hot", get("MacLeod")["priority"] == "hot" and len([p for p in res["people"] if "MacLeod" in p["name"]]) == 1),
     ("M_S09 Keith: his own demo", get("Urban")["next_step"] == "demo"), ("M_S10 Sarah: her own pricing", get("Lin")["next_step"] == "pricing" and "$34" in body("Lin")),
     ("M_S11 Élise: from Nadia, in French", get("Thibodeau")["sender"] == "Nadia" and get("Thibodeau")["french"]), ("M_S12 Dominic: falls back to badge address", D[id(get("dominic".title()))]["to"].startswith("droy@miramichi")),
     ("M_S13 Nathan: hot (rule says warm, Owen calls)", get("Drake")["priority"] == "hot"), ("M_S14 Brenda: call-back, no demo link", get("O'Neil")["next_step"] == "call back" and "[DEMO" not in body("O'Neil")),
     ("M_S15 Claude: separate person, thank-you", get("Claude")["next_step"] == "thank-you note")]
for t, ok in c: print("PASS" if ok else "DIFF", t)
print(sum(1 for _, ok in c if ok), "of 15")
