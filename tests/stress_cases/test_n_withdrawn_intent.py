"""N: when someone takes it back."""
from _harness import *
def t(cid, title, note, step):
    @case(cid, title, "Attack A-V", f"No {step} draft", True)
    def f():
        s = show([scan("S1", "Nan", "Tay", "Tay Clinic", "n@t.ca", note="")], voice=[(f"Nan Tay at Tay Clinic. {note}", "2026-10-20 11:00")]); r = row(s, "Nan"); return short(r), r["next_step"] != step
    return f
t("N1", "'wanted a demo but changed her mind'", "She wanted a demo but changed her mind, no demo.", "demo")
t("N2", "'not interested in a demo anymore'", "She's not interested in a demo anymore.", "demo")
t("N3", "'cancel the trial'", "Cancel the trial, she decided against it.", "trial")
t("N4", "'doesn't want pricing'", "She doesn't want pricing.", "pricing")
@case("N5", "An earlier 'no demo', then a later clear ask", "Attack A-V", "Demo: the newer clear ask wins")
def n5():
    s = show([scan("S1", "Nan", "Tay", "Tay Clinic", "n@t.ca", note="no demo", at="2026-10-20 09:00")], voice=[("Nan Tay at Tay Clinic came back, actually wants a demo now", "2026-10-21 15:00")]); r = row(s, "Nan"); return short(r), r["next_step"] == "demo"
@case("N6", "'still no demo from Toronto' means an unkept promise", "Attack A-V", "Stays a demo: not a withdrawal")
def n6():
    s = show([scan("S1", "Nan", "Tay", "Tay Clinic", "n@t.ca", note="")], lines=["Nan Tay AGAIN - still no demo from Toronto, wants one"]); r = row(s, "Nan"); return short(r), r["next_step"] == "demo"
if __name__ == "__main__": main()
