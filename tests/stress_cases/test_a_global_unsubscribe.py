"""A: someone who asked off stays off, whatever comes next."""
from _harness import *
DEMO = "book a demo"
@case("A1", "Old address removed, rescanned with a new address", "Attack A-V", "No draft; high-risk flag naming the match", True, "unsubscribe")
def a1():
    s = show([scan("S1", "Ann", "Lee", "Willow Physio", "new@willow.ca", note=DEMO)], mem=[dne("Ann Lee", "old@willow.ca", "Willow Physio")])
    r = row(s, "Ann"); return short(r), not r["body"] and "HIGH RISK" in r["status"] and "Matched on" in r["status"]
@case("A2", "Removed, then the clinic changed name and the address too", "Attack A-V", "No draft; flagged as identity unsure for Erin", True, "unsubscribe")
def a2():
    s = show([scan("S1", "Ann", "Lee", "Northshore Rehab", "ann@northshore.ca", note=DEMO)], mem=[dne("Ann Lee", "old@willow.ca", "Willow Physio")])
    r = row(s, "Ann"); return short(r), not r["body"] and "identity unsure" in r["status"]
@case("A3", "Same name, different person at a different clinic", "Attack A-V", "Not treated as removed: waits for Erin, and after 'Different person' gets a draft", True)
def a3():
    s = show([scan("S1", "Ann", "Lee", "Northshore Rehab", "ann@northshore.ca", note=DEMO)], mem=[dne("Ann Lee", "old@willow.ca", "Willow Physio")],
             decisions=[dict(person="Ann Lee", clinic="Northshore Rehab", decision="Different", by="Erin", date="2026-10-22")])
    r = row(s, "Ann"); return short(r), bool(r["body"]) and person(s, "Ann").get("dne") is not True
@case("A4", "Same address, different name", "Attack A-V", "No draft: an address match is enough", True, "unsubscribe")
def a4():
    s = show([scan("S1", "Bob", "Ng", "Willow Physio", "old@willow.ca", note=DEMO)], mem=[dne("Ann Lee", "old@willow.ca", "Willow Physio")])
    return no_draft(s, "Bob")
@case("A5", "Removed, then a new demo ask, a voice note and a booking", "Attack A-V", "No draft, whatever the sales signals say", True, "unsubscribe")
def a5():
    s = show([scan("S1", "Ann", "Lee", "Willow Physio", "old@willow.ca", note=DEMO)], cards=[card("C1", "Ann Lee", "Willow Physio", "old@willow.ca", "Nadia promised a demo", by="Nadia")],
             voice=[("Ann Lee at Willow Physio, great chat, wants a demo asap", "2026-10-20 11:00")], activity=[ev("E1", "2026-10-25 10:00", "demo booked", "Ann Lee", "old@willow.ca", "Willow Physio")],
             mem=[dne("Ann Lee", "old@willow.ca", "Willow Physio")], today="2026-10-26")
    return no_draft(s, "Ann")
@case("A6", "Typing OK or a sender on a confirmed removal", "Attack A-V", "Still no draft: nothing typed releases the list", True, "unsubscribe")
def a6():
    s = show([scan("S1", "Ann", "Lee", "Willow Physio", "old@willow.ca", note=DEMO)], mem=[dne("Ann Lee", "old@willow.ca", "Willow Physio")],
             decisions=[dict(person="Ann Lee", clinic="Willow Physio", decision="OK", by="Erin", date="")])
    return no_draft(s, "Ann")
@case("A7", "'Different person' typed on a confirmed removal", "Attack A-V", "Still no draft: Different only works on 'might be'", True, "unsubscribe")
def a7():
    s = show([scan("S1", "Ann", "Lee", "Willow Physio", "old@willow.ca", note=DEMO)], mem=[dne("Ann Lee", "old@willow.ca", "Willow Physio")],
             decisions=[dict(person="Ann Lee", clinic="Willow Physio", decision="Different", by="Erin", date="")])
    return no_draft(s, "Ann")
if __name__ == "__main__": main()
