"""L: same name is not same person."""
from _harness import *
@case("L1", "Two Lee Roys at two clinics", "Attack A-V", "Two people, each with their own ask", True, "crossperson")
def l1():
    s = show([scan("S1", "Lee", "Roy", "Harbour Clinic", "a@h.ca", note="demo"), scan("S2", "Lee", "Roy", "Bay Clinic", "b@bay.ca", note="pricing")]); got = [(p["clinic"], p["next_step"]) for p in s["res"]["people"]]; return str(got), sorted(got) == [("Bay Clinic", "pricing"), ("Harbour Clinic", "demo")]
@case("L2", "Voice note 'Lee Roy wants a demo', two Lee Roys, no clinic named", "Attack A-V", "Given to neither; a person places it", True, "crossperson")
def l2():
    s = show([scan("S1", "Lee", "Roy", "Harbour Clinic", "a@h.ca", note="chat"), scan("S2", "Lee", "Roy", "Bay Clinic", "b@bay.ca", note="chat")], voice=[("Lee Roy wants a demo", "2026-10-20 11:00")])
    return f"{[p['next_step'] for p in s['res']['people']]} general={len(s['res']['general'])}", all(p["next_step"] != "demo" for p in s["res"]["people"]) and len(s["res"]["general"]) == 1
@case("L3", "Same, but the note names the clinic", "Attack A-V", "Goes to the right Lee Roy")
def l3():
    s = show([scan("S1", "Lee", "Roy", "Harbour Clinic", "a@h.ca", note="chat"), scan("S2", "Lee", "Roy", "Bay Clinic", "b@bay.ca", note="chat")], voice=[("Lee Roy at Bay Clinic wants a demo", "2026-10-20 11:00")])
    got = {p["clinic"]: p["next_step"] for p in s["res"]["people"]}; return str(got), got["Bay Clinic"] == "demo" and got["Harbour Clinic"] != "demo"
@case("L4", "Two people sharing info@ at one clinic", "Attack A-V", "Two people, not merged by the shared inbox", True, "crossperson")
def l4():
    s = show([scan("S1", "Ann", "Hall", "Same Clinic", "info@same.ca", note="demo"), scan("S2", "Bob", "Hall", "Same Clinic", "info@same.ca", note="pricing")]); return str([p["name"] for p in s["res"]["people"]]), len(s["res"]["people"]) == 2
@case("L5", "Same surname, different clinics", "Attack A-V", "Two people")
def l5():
    s = show([scan("S1", "Dominic", "Roy", "Miramichi Wellness", "d@m.ca", note="chat"), scan("S2", "Claude", "Roy", "Bayside Massage", "c@b.ca", note="chat")]); return str([p["name"] for p in s["res"]["people"]]), len(s["res"]["people"]) == 2
if __name__ == "__main__": main()
