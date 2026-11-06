"""B: consent is its own gate. What someone wants never opens it."""
from _harness import *
def held(r, *need):
    return not r["body"] and r["status"].startswith("HOLD — LEGAL REVIEW REQUIRED") and all(n in r["status"] for n in need)
@case("B1", "N flag + asked for a demo at the booth", "Consent", "HOLD — LEGAL REVIEW REQUIRED, no draft, shows consent and the ask", True, "consent")
def b1():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "N", note="")], voice=[("Bea Oak at Oak Rehab, wants a demo", "2026-10-20 11:00")])
    r = row(s, "Bea"); return short(r), held(r, "consent = N", "demo")
@case("B2", "N flag + card + asked for pricing", "Consent", "HOLD, no draft", True, "consent")
def b2():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "N", note="")], cards=[card("C1", "Bea Oak", "Oak Rehab", "b@o.ca", "")], voice=[("Bea Oak at Oak Rehab, wants pricing", "2026-10-20 11:00")])
    r = row(s, "Bea"); return short(r), held(r, "consent = N", "pricing", "card")
@case("B3", "Y flag + 'No marketing emails, just send quote'", "Consent", "Plain price only: no demo link, trial, or list. Flagged for Erin", True, "consent")
def b3():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "Y", note="")], cards=[card("C1", "Bea Oak", "Oak Rehab", "b@o.ca", "No marketing emails, just send quote")])
    r = row(s, "Bea"); return short(r) + " body=" + r["body"], r["next_step"] == "pricing" and "$34" in r["body"] and not re.search(r"\[|http|newsletter", r["body"]) and any("Erin checks" in f for f in r["p"]["flags"])
@case("B4", "Y flag + clear demo ask", "Consent", "Normal demo draft (the gate doesn't block people who consented)")
def b4():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "Y", note="please book a demo")])
    r = row(s, "Bea"); return short(r), bool(r["body"]) and r["next_step"] == "demo"
@case("B5", "N flag + asked for a trial", "Consent", "HOLD, no draft", True, "consent")
def b5():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "N", note="")], voice=[("Bea Oak at Oak Rehab, wants a trial", "2026-10-20 11:00")])
    r = row(s, "Bea"); return short(r), held(r, "trial")
@case("B6a", "Y flag, then an event says consent was withdrawn", "Consent", "No draft", True, "consent")
def b6a():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "Y", note="book a demo")], activity=[ev("E1", "2026-10-21 10:00", "consent withdrawn", "Bea Oak", "b@o.ca", "Oak Rehab")])
    return no_draft(s, "Bea")
@case("B6b", "Y flag, then a reply says 'do not contact me again'", "Consent", "No draft, and on the list for later shows", True, "consent")
def b6b():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "Y", note="book a demo")], activity=[ev("E1", "2026-10-21 10:00", "reply received", "Bea Oak", "b@o.ca", "Oak Rehab", "Please do not contact me again")])
    r = row(s, "Bea"); return short(r), not r["body"] and "b@o.ca" in open(s["memory"], encoding="utf8").read()
@case("B6c", "Y flag, then a note says she withdrew permission", "Consent", "No draft, and on the list", True, "consent")
def b6c():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "Y", note="book a demo")], voice=[("Bea Oak at Oak Rehab called back and withdrew her consent, do not email her", "2026-10-21 11:00")])
    r = row(s, "Bea"); return short(r), not r["body"] and "do not email" in open(s["memory"], encoding="utf8").read()
@case("B7", "N flag + someone types OK", "Consent", "Still held: only the law question releases it", True, "consent")
def b7():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "N", note="")], voice=[("Bea Oak at Oak Rehab, wants a demo", "2026-10-20 11:00")], decisions=[dict(person="Bea Oak", clinic="Oak Rehab", decision="OK", by="Erin", date="")])
    r = row(s, "Bea"); return short(r), held(r)
@case("B8", "N flag + 'no mailing list, just pricing' (the Amira case)", "Consent", "HOLD with the ask shown: the old bypass is gone", True, "consent")
def b8():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "N", note="")], voice=[("Bea Oak at Oak Rehab, no mailing list, just pricing", "2026-10-20 11:00")])
    r = row(s, "Bea"); return short(r), held(r, "pricing")
@case("B9", "The hold reaches Erin's page with its reason", "Consent", "Erin's view of the page shows consent = N and the ask")
def b9():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "N", note="")], voice=[("Bea Oak at Oak Rehab, wants a demo", "2026-10-20 11:00")])
    h = open(s["out"] + "/index.html", encoding="utf8").read(); erin = h[h.index('id="erin"'):]
    return "found in Erin's section: " + str("consent = N" in erin), "consent = N" in erin and "demo at the booth" in erin
for i, v in enumerate(["no", "FALSE", "0", "Opt-out", "declined"], 10):
    def mk(v=v):
        def f():
            s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", v, note="wants a demo")]); r = row(s, "Bea"); return short(r), held(r)
        return f
    case(f"B{i}", f"Share column says {v!r}", "Consent", "Held", True, "consent")(mk())
@case("B15", "Share column blank or unclear", "Consent", "No draft until someone checks", True, "consent")
def b15():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", "maybe", note="wants a demo")]); return no_draft(s, "Bea")
@case("B16", "'no emails please, phone only'", "Consent", "A call reminder and no email text at all", True, "consent")
def b16():
    s = show([scan("S1", "Bea", "Oak", "Oak Rehab", "b@o.ca", note="")], voice=[("Bea Oak at Oak Rehab, no emails please, phone only", "2026-10-20 11:00")]); r = row(s, "Bea"); return short(r), r["status"].startswith("CALL") and not r["body"]
if __name__ == "__main__": main()
