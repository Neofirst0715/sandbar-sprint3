"""G: personal remarks never leave. Checked in every file written, not only the drafts."""
from _harness import *
def go(text, **k): return show([scan("S1", "Gil", "Pine", "Pine Clinic", "g@p.ca", note="")], voice=[(f"Gil Pine at Pine Clinic. {text}", "2026-10-20 11:00")], **k)
def t(cid, title, text, pat):
    @case(cid, title, "Privacy", f"'{pat}' in no draft, CSV, Sheet or page", True, "privacy")
    def f():
        s = go(text); l = leaks(s, r"\b(" + pat + r")\b"); return f"body={row(s, 'Gil')['body']!r} leaks={l}", not l
    return f
t("G1", "Partner suing her", "Her clinic is in trouble because her partner is suing her, don't mention that.", "suing|in trouble")
t("G2", "Wife's surgery", "His wife had surgery in Moncton hospital so he looked distracted.", "surgery|hospital|wife|distracted")
t("G5", "Divorce", "She is going through a divorce, wants a demo.", "divorce")
t("G6", "Chemo", "He told me he is going through chemo, wants a demo.", "chemo")
t("G7", "Laid off and crying", "She got laid off and cried at the booth, wants a trial.", "laid off|cried")
t("G8", "Money and drink", "Her husband drinks and the clinic is nearly bankrupt, wants pricing.", "drinks|bankrupt|husband")
@case("G3", "'They hate Clinivo because customer support was rude'", "Privacy", "Keeps the business fact (on Clinivo); the complaint's words stay out", True, "privacy")
def g3():
    s = go("They hate Clinivo because customer support was rude to them."); l = leaks(s, r"\brude\b|\bhate\b"); return f"body={row(s, 'Gil')['body']!r} leaks={l}", "Clinivo" in row(s, "Gil")["body"] and not l
@case("G4", "'His business partner wants the pricing in writing' (reverse test)", "Privacy", "Kept: a business partner isn't private. Pricing draft mentions the partner", True)
def g4():
    s = go("His business partner wants the pricing in writing."); r = row(s, "Gil"); return f"step={r['next_step']} body={r['body']!r}", r["next_step"] == "pricing" and "business partner" in r["body"]
@case("G9", "Personal remark on the scan note, the card and the list", "Privacy", "In none of the files", True, "privacy")
def g9():
    s = show([scan("S1", "Gil", "Pine", "Pine Clinic", "g@p.ca", note="his wife had surgery, wants a demo")], cards=[card("C1", "Gil Pine", "Pine Clinic", "g@p.ca", "going through a divorce. demo")], lines=["Gil Pine, chemo starts in May", "Zed Nobody in Nowhere, her son is in hospital"])
    l = leaks(s, r"\b(surgery|divorce|chemo|hospital)\b"); return f"leaks={l}", not l
@case("G10", "Raw notes aren't left among the results", "Privacy", "No raw copy of the notes in the results folder", True, "privacy")
def g10():
    s = go("His wife had surgery."); fs = sorted(files_text(s["out"])); return str(fs), not any("_input" in f or "booth-notes" in f for f in fs)
@case("G11", "A remark the word lists don't know", "Privacy", "Doesn't appear: exports are built from facts, not the note's words", True, "privacy")
def g11():
    s = go("Word is his brother-in-law owes half of Halifax money, wants a demo."); l = leaks(s, r"owes half"); return f"body={row(s, 'Gil')['body']!r} leaks={l}", not l
@case("G12", "A finished draft contains a personal word", "Privacy", "Not offered: PRIVACY REVIEW REQUIRED, Erin told", True, "privacy")
def g12():
    old = drafts.build_draft
    drafts.build_draft = lambda p, show_, st, late: dict(subject="x", body="Gil, sorry about the surgery. Owen.", notes=[])
    try: s = go("wants a demo")
    finally: drafts.build_draft = old
    r = row(s, "Gil"); return short(r), r["status"].startswith("PRIVACY") and not r["body"] and any("privacy review" in f for f in r["p"]["flags"])
@case("G13", "Output audit finds a leak planted in a file", "Privacy", "The audit reports it", True)
def g13():
    import tempfile as tf
    d = tf.mkdtemp(); open(d + "/x.csv", "w").write("Her partner is suing her badly"); return str(privacy.audit_outputs(d, ["partner is suing her"])), bool(privacy.audit_outputs(d, ["partner is suing her"]))
@case("G14", "Ordinary business words", "Privacy", "Uses Clinivo and wants less admin: kept, nothing flagged")
def g14():
    s = go("On Clinivo, wants less admin and better booking."); p = person(s, "Gil"); return f"detail={p['safe_detail']!r}", "Clinivo" in p["safe_detail"] and not p["private_raw"]
for i, t_ in enumerate(["her partner left her last month", "he's been off sick for months", "her mom passed in the fall so it's been rough", "said the clinic might fold because he owes the bank", "she has MS and uses a cane", "he's in AA", "she's expecting in June", "he was arrested last year"], 20):
    def mk(t_=t_):
        def f():
            s = go(t_ + ", wants a demo"); l = leaks(s, re.escape(t_)); return f"step={row(s, 'Gil')['next_step']} leaks={l}", not l and row(s, "Gil")["next_step"] == "demo"
        return f
    case(f"G{i}", f"Remark no word list was written for: '{t_}'", "Privacy", "The remark is in no file; the demo ask still works", True, "privacy")(mk())
if __name__ == "__main__": main()
