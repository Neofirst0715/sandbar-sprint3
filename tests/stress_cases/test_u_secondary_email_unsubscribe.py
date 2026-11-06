"""U: removal on any address a person has used, carried to later shows."""
from _harness import *
BOTH = dict(scans=[scan("S1", "Ann", "Lee", "Willow Physio", "primary@w.ca", note="book a demo")], cards=[card("C1", "Ann Lee", "Willow Physio", "second@w.ca", "demo")])
@case("U1", "List has the badge address; card has another", "Attack A-V", "No draft to the other address", True, "unsubscribe")
def u1():
    s = show(**BOTH, mem=[dne("X", "primary@w.ca", "")]); return no_draft(s, "Ann")
@case("U2", "Remove-me reply from the second address", "Attack A-V", "No draft", True, "unsubscribe")
def u2():
    s = show(**BOTH, activity=[ev("E1", "2026-10-21 10:00", "reply received", "Ann Lee", "second@w.ca", "Willow Physio", "please remove me")]); return no_draft(s, "Ann")
@case("U3", "Case and spaces differ from the list", "Attack A-V", "No draft", True, "unsubscribe")
def u3():
    s = show([scan("S1", "Ann", "Lee", "Willow Physio", " WITH.CASE@w.ca ", note="book a demo")], mem=[dne("X", "with.case@w.ca", "")]); return no_draft(s, "Ann")
@case("U4", "Removal at one show, new address at the next", "Attack A-V", "Blocked at the next show, through memory.csv", True, "unsubscribe")
def u4():
    m = tempfile.mktemp(suffix=".csv")
    show([scan("S1", "Ann", "Lee", "Willow Physio", "first@w.ca", note="demo")], activity=[ev("E1", "2026-10-21 10:00", "reply received", "Ann Lee", "first@w.ca", "Willow Physio", "take me off your list")], memfile=m, name="Show One")
    s2 = show([scan("S1", "Ann", "Lee", "Willow Physio", "brand.new@w.ca", note="book a demo", at="2027-02-10 10:00")], today="2027-02-12", memfile=m, name="Show Two"); return no_draft(s2, "Ann")
@case("U5", "A confirmed match with a new address", "Attack A-V", "The new address joins the list", True, "unsubscribe")
def u5():
    s = show([scan("S1", "Ann", "Lee", "Willow Physio", "new@w.ca", note="demo")], mem=[dne("Ann Lee", "old@w.ca", "Willow Physio")]); t = open(s["memory"], encoding="utf8").read(); return "new@w.ca on list: " + str("new@w.ca" in t and "do not email" in t), any(r["email"] == "new@w.ca" and r["status"] == "do not email" for r in csv.DictReader(open(s["memory"], encoding="utf8")))
if __name__ == "__main__": main()
