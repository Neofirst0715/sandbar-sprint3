"""J: reaching someone. No usable address means a phone reminder, or Erin."""
from _harness import *
@case("J1", "Jean-François Lévesque, email N/A, phone with extension", "Attack A-V", "No draft, call reminder, name and extension intact", True, "invalidemail")
def j1():
    s = show([scan("S1", "Jean-François", "Lévesque", "Lev Clinic", "N/A", note="wants a demo", phone="506-555-0100 ext 4")]); r = row(s, "Jean"); c = r["p"].get("call_instead", "")
    return f"{short(r)} | {c}", not r["body"] and r["status"].startswith("CALL") and "ext 4" in c and "Jean-François Lévesque" in c
@case("J2", "No email and no phone", "Attack A-V", "No draft; Erin asked to find a contact", True, "invalidemail")
def j2():
    s = show([scan("S1", "Jo", "Lev", "Lev Clinic", "", note="wants a demo")]); r = row(s, "Jo"); return f"{short(r)} {r['p']['flags']}", not r["body"] and any("Erin" in f for f in r["p"]["flags"])
@case("J3", "The call reminder reaches the sender's page", "Attack A-V", "On Owen's page, under Call, with the number")
def j3():
    s = show([scan("S1", "Jean", "Lev", "Lev Clinic", "N/A", note="wants a demo", phone="506-555-0100 ext 4")]); h = open(s["out"] + "/index.html", encoding="utf8").read(); ow = h[h.index('id="owen"'):h.index('id="erin"')]
    return "found: " + str("ext 4" in ow), "ext 4" in ow
@case("J4", "Phone says N/A too", "Attack A-V", "Treated as no phone", True, "invalidemail")
def j4():
    s = show([scan("S1", "Jo", "Lev", "Lev Clinic", "N/A", note="wants a demo", phone="N/A")]); r = row(s, "Jo"); return short(r), r["status"].startswith("NO DRAFT")
if __name__ == "__main__": main()
