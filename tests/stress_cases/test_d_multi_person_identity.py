"""D: several people at one clinic stay several people."""
from _harness import *
def apex(): return show([scan("S1", "Keith", "Urban", "Apex Health", "k@apex.ca", note="demo request", rating="A"), scan("S2", "Sarah", "Lin", "Apex Health", "s@apex.ca", note="pricing in writing"), scan("S3", "Pat", "Ray", "Apex Health", "p@apex.ca", note="draw only")])
@case("D1", "Three people at Apex: demo, pricing, draw only", "Attack A-V", "Keith demo draft, Sarah pricing draft, the third excluded; nobody merged", True, "crossperson")
def d1():
    s = apex(); k, a = row(s, "Keith"), row(s, "Sarah"); return f"{short(k)} | {short(a)} | Pat: {short(row(s, 'Pat'))}", k["next_step"] == "demo" and a["next_step"] == "pricing" and row(s, "Pat") is None and len(s["res"]["people"]) == 3
@case("D2", "Keith's draft has nothing of Sarah's, and the other way", "Attack A-V", "No demo link for Sarah, no price for Keith", True, "crossperson")
def d2():
    s = apex(); k, a = row(s, "Keith"), row(s, "Sarah"); return f"Keith: {k['body']} | Sarah: {a['body']}", "$34" not in k["body"] and "[DEMO" not in a["body"] and "Sarah" not in k["body"] and "Keith" not in a["body"]
@case("D3", "One voice sentence: Keith wants a demo and Sarah wants pricing", "Attack A-V", "Each gets their own ask", True, "crossperson")
def d3():
    s = show([scan("S1", "Keith", "Urban", "Apex Health", "k@apex.ca", note=""), scan("S2", "Sarah", "Lin", "Apex Health", "s@apex.ca", note="")], voice=[("At Apex Health, Keith Urban wants a demo and Sarah Lin wants the pricing in writing.", "2026-10-20 11:00")])
    k, a = row(s, "Keith"), row(s, "Sarah"); return f"{short(k)} | {short(a)}", k["next_step"] == "demo" and a["next_step"] == "pricing"
@case("D4", "One voice sentence that can't be separated: 'both want a demo'", "Attack A-V", "Given to neither; goes to a person to place", True, "crossperson")
def d4():
    s = show([scan("S1", "Keith", "Urban", "Apex Health", "k@apex.ca", note=""), scan("S2", "Sarah", "Lin", "Apex Health", "s@apex.ca", note="")], voice=[("Keith Urban and Sarah Lin both want a demo.", "2026-10-20 11:00")])
    k, a = row(s, "Keith"), row(s, "Sarah"); return f"{k['next_step']}/{a['next_step']} general={s['res']['general']}", k["next_step"] != "demo" and a["next_step"] != "demo" and len(s["res"]["general"]) == 1
@case("D5", "'Jen Lee and Ravi Das want a demo'", "Attack A-V", "Both get the demo: a shared ask is clear")
def d5():
    s = show([scan("S1", "Jen", "Lee", "Apex Health", "j@apex.ca", note=""), scan("S2", "Ravi", "Das", "Apex Health", "r@apex.ca", note="")], voice=[("Jen Lee and Ravi Das want a demo.", "2026-10-20 11:00")])
    return f"{row(s, 'Jen')['next_step']}/{row(s, 'Ravi')['next_step']}", row(s, "Jen")["next_step"] == "demo" and row(s, "Ravi")["next_step"] == "demo"
if __name__ == "__main__": main()
