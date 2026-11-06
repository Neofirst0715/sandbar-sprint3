"""M: a removal survives changes in how the name or clinic is written."""
from _harness import *
def t(cid, title, f_, l_, co, listname, listco):
    @case(cid, title, "Attack A-V", "No draft", True, "unsubscribe")
    def go():
        s = show([scan("S1", f_, l_, co, "new@w.ca", note="book a demo")], mem=[dne(listname, "old@w.ca", listco)]); r = row(s, f_[:3]); return short(r), not r["body"] and "HIGH RISK" in r["status"]
    return go
t("M1", "Accents dropped", "Rene", "Levesque", "Willow Physio", "René Lévesque", "Willow Physio")
t("M2", "Hyphenated surname", "Ann", "Lee-Hart", "Willow Physio", "Ann Lee", "Willow Physio")
t("M3", "Spelling change", "Katherine", "Murphy", "Willow Physio", "Kathryn Murphey", "Willow Physio")
t("M4", "Longer clinic name", "Ann", "Lee", "Willow Physiotherapy & Wellness", "Ann Lee", "Willow Physio")
t("M5", "Clinic abbreviated", "Ann", "Lee", "WP Massage", "Ann Lee", "Willow Physio & Massage")
t("M6", "Nickname", "Liz", "Burke", "Willow Physio", "Elizabeth Burke", "Willow Physio")
t("M7", "Title on the name", "Dr. Ann", "Lee", "Willow Physio", "Ann Lee, PT", "Willow Physio")
t("M8", "First and last swapped", "Lee", "Ann", "Willow Physio", "Ann Lee", "Willow Physio")
t("M9", "Surname spelled differently, same first name and clinic", "Ann", "Li", "Willow Physio", "Ann Lee", "Willow Physio")
t("M10", "Initial for a first name", "A.", "Lee", "Willow Physio", "Ann Lee", "Willow Physio")
@case("M11", "A colleague at the same clinic, different name", "Attack A-V", "Not blocked: the clinic alone isn't a match", True)
def m11():
    s = show([scan("S1", "Bob", "Stone", "Willow Physio", "bob@w.ca", note="book a demo")], mem=[dne("Ann Lee", "old@w.ca", "Willow Physio")]); r = row(s, "Bob"); return short(r), bool(r["body"])
if __name__ == "__main__": main()
