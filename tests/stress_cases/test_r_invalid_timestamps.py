"""R: a bad date on one record can't sink a show or sneak into the counts."""
from _harness import *
A = [scan("S1", "Rae", "Oak", "Oak Clinic", "r@o.ca", note="demo")]
for i, w in enumerate(["banana", "", "13/13/2026", "05/06/2026 10:00", "2026-13-45"], 1):
    def mk(w=w):
        def f():
            s = show(A, activity=[ev("E1", w, "demo booked", "Rae Oak", "r@o.ca", "Oak Clinic")], today="2026-12-01"); p = person(s, "Rae")
            return f"pile={p['pile']}; issues={[x['reason'] for x in issues(s)]}", p["pile"] == "never written to" and any("Can't read the date" in x["reason"] for x in issues(s))
        return f
    case(f"R{i}", f"Booking dated '{w}'", "Day 30", "No crash; not counted; listed with its record ID for Erin", True, "window")(mk())
@case("R6", "A send with a bad date", "Day 30", "Not counted in the piles; no second email offered", True, "window")
def r6():
    s = show(A, activity=[ev("E1", "banana", "email sent", "Rae Oak", "r@o.ca", "Oak Clinic")], today="2026-12-01"); p = person(s, "Rae"); r = row(s, "Rae"); return f"pile={p['pile']}; {short(r)}", p["pile"] == "never written to" and r["status"].startswith("ALREADY")
@case("R7", "One bad row among good ones", "Day 30", "The good row still counts", True)
def r7():
    s = show(A + [scan("S2", "Ren", "Ash", "Ash Clinic", "n@a.ca", note="demo")], activity=[ev("E1", "banana", "demo booked", "Rae Oak", "r@o.ca", "Oak Clinic"), ev("E2", "2026-10-25 10:00", "demo booked", "Ren Ash", "n@a.ca", "Ash Clinic")], today="2026-12-01")
    return f"{person(s, 'Rae')['pile']} / {person(s, 'Ren')['pile']}", person(s, "Ren")["pile"] == "booked a demo" and person(s, "Rae")["pile"] == "never written to"
if __name__ == "__main__": main()
