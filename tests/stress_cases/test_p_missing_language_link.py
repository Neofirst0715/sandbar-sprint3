"""P: a link that isn't set yet."""
from _harness import *
FR = dict(scans=[scan("S1", "Ana", "Dubé", "Dube Clinic", "a@d.ca", note="", by="Nadia")], voice=[("c'est Nadia, Ana Dubé, Dube Clinic, en français, elle veut une démo", "2026-10-20 11:00")])
@case("P1", "French demo with no demo link set", "Attack A-V", "Yellow marker shown, never a blank; the page says links are missing")
def p1():
    s = show(**FR); r = row(s, "Ana"); h = open(s["out"] + "/index.html", encoding="utf8").read(); return r["body"], "[DEMO LINK]" in r["body"] and "Links not set yet" in h and "<mark>[DEMO LINK]</mark>" in h
@case("P2", "Same, with the link set", "Attack A-V", "Link in the French draft")
def p2():
    s = show(**FR, settings=dict(demo_link="https://x/demo")); r = row(s, "Ana"); return r["body"], "https://x/demo" in r["body"]
@case("P3", "Security document asked for, none set", "Attack A-V", "No draft that pretends: Owen calls", True)
def p3():
    s = show([scan("S1", "Nat", "Drake", "Drake Rehab", "n@d.ca", note="urgent: SOC2 and IT security spec")]); r = row(s, "Nat"); return short(r), not r["body"] and r["status"].startswith("CALL")
@case("P4", "Security document asked for, link set", "Attack A-V", "Draft with the link")
def p4():
    s = show([scan("S1", "Nat", "Drake", "Drake Rehab", "n@d.ca", note="urgent: SOC2 and IT security spec")], settings=dict(security_doc="https://x/sec")); r = row(s, "Nat"); return r["body"], "https://x/sec" in r["body"]
if __name__ == "__main__": main()
