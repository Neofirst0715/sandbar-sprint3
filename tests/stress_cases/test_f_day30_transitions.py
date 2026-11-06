"""F: people move between piles over the month."""
from _harness import *
A = [scan("S1", "Fay", "Elm", "Elm Clinic", "f@e.ca", note="wants a look at it")]
E_ = lambda i, w, e: ev(i, w, e, "Fay Elm", "f@e.ca", "Elm Clinic")
def go(*evs): return show(A, activity=list(evs), today="2026-12-01")
@case("F1", "Written to, then trial, then demo", "Day 30", "One pile: booked a demo", True, "duplicate")
def f1():
    s = go(E_("1", "2026-10-22 10:00", "email sent"), E_("2", "2026-10-25 10:00", "trial started"), E_("3", "2026-10-27 10:00", "demo booked"))
    c = sum(1 for l in open(s["out"] + "/piles.csv", encoding="utf8")) - 1; return f"{person(s, 'Fay')['pile']}, {c} row", person(s, "Fay")["pile"] == "booked a demo" and c == 1
@case("F2", "Written to, and it bounced", "Day 30", "Never written to; Owen phones")
def f2():
    s = go(E_("1", "2026-10-22 10:00", "email sent"), E_("2", "2026-10-22 11:00", "email bounced")); r = row(s, "Fay"); return f"{person(s, 'Fay')['pile']}; {short(r)}", person(s, "Fay")["pile"] == "never written to" and not r["body"]
@case("F3", "Booked, then cancelled", "Day 30", "Still counts (booked by day 30 counts), flagged for Erin")
def f3():
    s = go(E_("1", "2026-10-22 10:00", "demo booked"), E_("2", "2026-10-23 10:00", "demo cancelled")); p = person(s, "Fay"); return f"{p['pile']}; {p['flags']}", p["pile"] == "booked a demo" and any("cancelled" in f for f in p["flags"])
@case("F4", "Second run after a booking", "Day 30", "No booking link offered again")
def f4():
    s = go(E_("1", "2026-10-22 10:00", "demo booked")); r = row(s, "Fay"); return short(r) + " " + r["body"][:60], "[DEMO" not in r["body"]
if __name__ == "__main__": main()
