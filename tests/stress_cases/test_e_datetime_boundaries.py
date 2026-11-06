"""E: the 30-day window uses full times. Rule: first scan <= event <= last scan + 30 days, end included."""
from _harness import *
A = [scan("S1", "Eve", "Elm", "Elm Clinic", "e@e.ca", note="wants to think", at="2026-10-20 09:00"), scan("S2", "Eli", "Ash", "Ash Clinic", "a@a.ca", note="chat", at="2026-10-21 17:00")]
def pile(when, e="demo booked"):
    s = show(A, activity=[ev("E1", when, e, "Eve Elm", "e@e.ca", "Elm Clinic")], today="2026-12-30"); return person(s, "Eve")["pile"], s
def t(cid, title, when, want, metric):
    @case(cid, title, "Day 30", f"Pile = {want}", True, metric)
    def f():
        got, _ = pile(when); return f"booking {when} -> {got}", got == want
    return f
t("E1", "Show starts 09:00, booking 02:00 the same day", "2026-10-20 02:00", "never written to", "preshow")
t("E2", "Booking Nov 25, well after the window", "2026-11-25 10:00", "never written to", "window")
t("E3", "Booking inside the window", "2026-11-19 10:00", "booked a demo", "window")
t("E4a", "Booking exactly at the deadline (Oct 21 17:00 + 30 days)", "2026-11-20 17:00", "booked a demo", "window")
t("E4b", "One minute after the deadline", "2026-11-20 17:01", "never written to", "window")
t("E4c", "Later on the deadline day", "2026-11-20 23:00", "never written to", "window")
t("E6", "Booking during the show", "2026-10-20 15:00", "booked a demo", "window")
@case("E5", "Booking with an unreadable time", "Day 30", "No crash, not counted, listed for Erin with the raw text", True, "window")
def e5():
    got, s = pile("sometime soon"); i = issues(s); return f"{got}; issues={[x['reason'] for x in i]}", got == "never written to" and any("sometime soon" in x["reason"] for x in i)
@case("E7", "Email sent before the show", "Day 30", "Not counted as written to, and doesn't stop a draft", True, "preshow")
def e7():
    got, s = pile("2026-10-01 10:00", "email sent"); r = row(s, "Eve"); return f"{got}; {short(r)}", got == "never written to" and not r["status"].startswith("ALREADY")
@case("E8", "Email sent after the window", "Day 30", "Not in the piles, but nobody is offered a second email", True, "window")
def e8():
    got, s = pile("2026-12-25 10:00", "email sent"); r = row(s, "Eve"); return f"{got}; {short(r)}", got == "never written to" and r["status"].startswith("ALREADY")
@case("E9", "Date with no time, on the deadline day", "Day 30", "Counted by the written default, flagged for Erin with the raw date")
def e9():
    got, s = pile("2026-11-20"); return f"{got}; flags={person(s, 'Eve')['flags']}", got == "booked a demo" and any("2026-11-20" in f for f in person(s, "Eve")["flags"])
@case("E10", "Raw time kept for Erin", "Day 30", "Evidence shows the booking's own time")
def e10():
    got, s = pile("2026-10-25 10:30"); e_ = person(s, "Eve")["pile_evidence"]; return e_, "2026-10-25 10:30" in e_
@case("E11", "No readable show times at all", "Day 30", "Bookings not counted; Erin told why", True, "window")
def e11():
    s = show([scan("S1", "Eve", "Elm", "Elm Clinic", "e@e.ca", note="chat", at="not a date")], activity=[ev("E1", "2026-10-25 10:00", "demo booked", "Eve Elm", "e@e.ca", "Elm Clinic")], today="2026-12-30")
    i = issues(s); return f"{person(s, 'Eve')['pile']}; {[x['reason'] for x in i]}", person(s, "Eve")["pile"] == "never written to" and any("dates are unknown" in x["reason"] for x in i)
@case("E12", "Time with a zone offset", "Day 30", "Read as written, in the show's local time (rules.md)")
def e12():
    got, _ = pile("2026-10-25T10:00:00-03:00"); return got, got == "booked a demo"
if __name__ == "__main__": main()
