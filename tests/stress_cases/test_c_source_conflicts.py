"""C: when sources disagree. Consent and removal sit above all of this."""
from _harness import *
BASE = dict(scans=[scan("S1", "Cal", "Fir", "Fir Clinic", "c@f.ca", note="pricing?")], cards=[card("C1", "Cal Fir", "Fir Clinic", "c@f.ca", "trial with 2 staff")], voice=[("Cal Fir at Fir Clinic. Spoke with him later, actually book a demo asap", "2026-10-21 16:00")])
@case("C1", "Badge 'pricing?', card 'trial', later voice note 'book a demo'", "Attack A-V", "Next step demo; source conflict flagged; trial not lost")
def c1():
    s = show(**BASE); r = row(s, "Cal"); fl = r["p"]["flags"]
    return short(r) + f" flags={fl}", r["next_step"] == "demo" and any("Source conflict" in f and "trial" in f for f in fl)
@case("C2", "Older voice 'wants a demo', newer card withdraws it", "Attack A-V", "No demo draft; withdrawal flagged", True, "crossperson")
def c2():
    s = show([scan("S1", "Cal", "Fir", "Fir Clinic", "c@f.ca", note="")], cards=[card("C1", "Cal Fir", "Fir Clinic", "c@f.ca", "changed his mind, no demo")], voice=[("Cal Fir at Fir Clinic wants a demo", "2026-10-20 10:00")])
    r = row(s, "Cal"); return short(r), r["next_step"] != "demo" and "[DEMO" not in r["body"] and any("no longer want" in f for f in r["p"]["flags"])
@case("C3", "Conflict on someone with an N flag", "Consent", "Held: source order never overrides consent", True, "consent")
def c3():
    s = show([dict(BASE["scans"][0], share_with_exhibitors="N")], BASE["cards"], BASE["voice"]); r = row(s, "Cal"); return short(r), not r["body"] and r["status"].startswith("HOLD")
@case("C4", "Conflict on someone on the do-not-email list", "Attack A-V", "No draft: source order never overrides removal", True, "unsubscribe")
def c4():
    s = show(BASE["scans"], BASE["cards"], BASE["voice"], mem=[dne("Cal Fir", "c@f.ca", "Fir Clinic")]); return no_draft(s, "Cal")
@case("C5", "Sources disagree and no voice note settles it", "Attack A-V", "Waits on Owen: not guessed")
def c5():
    s = show([scan("S1", "Cal", "Fir", "Fir Clinic", "c@f.ca", note="wants pricing")], cards=[card("C1", "Cal Fir", "Fir Clinic", "c@f.ca", "wants a trial")]); r = row(s, "Cal")
    return short(r), r["status"].startswith("WAITING")
if __name__ == "__main__": main()
