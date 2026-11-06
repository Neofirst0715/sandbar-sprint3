"""Q: the same event twice is one event. Two different days are two."""
from _harness import *
A = [scan("S1", "Quinn", "Oak", "Oak Clinic", "q@o.ca", note="demo")]
B = ev("E1", "2026-10-25 10:00", "demo booked", "Quinn Oak", "q@o.ca", "Oak Clinic")
S_ = ev("S1", "2026-10-22 10:00", "email sent", "Quinn Oak", "q@o.ca", "Oak Clinic")
def piles_rows(s): return list(csv.DictReader(open(s["out"] + "/piles.csv", encoding="utf8")))
@case("Q1", "Same booking three times, two IDs", "Day 30", "One row in the piles", True, "duplicate")
def q1():
    s = show(A, activity=[B, B, dict(B, event_id="E2")], today="2026-12-01"); return f"{len(piles_rows(s))} row", len(piles_rows(s)) == 1
@case("Q2", "Same send twice, then a real send a week later", "Day 30", "Two sends kept", True, "duplicate")
def q2():
    s = show(A, activity=[S_, S_, dict(S_, event_id="S2", date_time="2026-10-29 10:00")], today="2026-12-01"); got = person(s, "Quinn")["sent"]; return str(got), len(got) == 2
@case("Q3", "Two sources log one event", "Day 30", "One")
def q3():
    s = show(A, activity=[S_, dict(S_, event_id="X9", channel="cc to hello")], today="2026-12-01"); got = person(s, "Quinn")["sent"]; return str(got), len(got) == 1
@case("Q4", "Same activity file dropped twice", "Day 30", "Counts unchanged", True, "duplicate")
def q4():
    def raw(d):
        import shutil; shutil.copy(d + "/after-show-activity.csv", d + "/copy of activity.csv")
    s = show(A, activity=[B], today="2026-12-01", raw=raw); return f"{len(piles_rows(s))} row", len(piles_rows(s)) == 1
if __name__ == "__main__": main()
