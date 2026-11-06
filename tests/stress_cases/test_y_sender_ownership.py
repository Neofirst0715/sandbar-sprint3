"""Y: each email goes from whoever had the conversation (Nadia and Owen, group call). Erin coordinates; she never sends."""
from _harness import *
def view(s, v):
    h = open(s["out"] + "/index.html", encoding="utf8").read(); order = ["nadia", "owen", "erin"]
    a = h.index(f'id="{v}"'); nxt = [h.index(f'id="{x}"') for x in order if h.index(f'id="{x}"') > a]
    return h[a:(min(nxt) if nxt else len(h))]
OWEN = scan("S11", "Lena", "Petrov", "Tidewater Physio", "lena@tide.ca", note="wants a demo", by="Owen")
NADIA = scan("S12", "Mia", "Dunn", "Dunn Clinic", "mia@dunn.ca", note="wants a demo", by="Nadia")
@case("Y1", "Owen's conversation", "Attack A-V", "Draft on Owen's page, signed Owen; not on Nadia's", True, "crossperson")
def y1():
    s = show([OWEN], cards=[card("C3", "Lena Petrov", "Tidewater Physio", "lena@tide.ca", "wants a demo", by="Owen")]); r = row(s, "Lena")
    return f"from={r['sender']} signed={r['body'].rstrip()[-6:]} on Owen: {'Lena' in view(s, 'owen')}; on Nadia: {'Lena' in view(s, 'nadia')}", r["sender"] == "Owen" and "Lena" in view(s, "owen") and "Lena" not in view(s, "nadia")
@case("Y2", "Nadia's conversation, with a card she collected", "Attack A-V", "Draft on Nadia's page, signed Nadia; not on Owen's", True, "crossperson")
def y2():
    s = show([NADIA], cards=[card("C4", "Mia Dunn", "Dunn Clinic", "mia@dunn.ca", "wants a demo", by="Nadia")]); r = row(s, "Mia")
    return f"from={r['sender']} on Nadia: {'Mia' in view(s, 'nadia')}; on Owen: {'Mia' in view(s, 'owen')}", r["sender"] == "Nadia" and "Mia" in view(s, "nadia") and "Mia" not in view(s, "owen")
@case("Y3", "Scan says pricing, card says demo, both Owen's (Lena's case)", "Attack A-V", "Not treated as settled: waits on Owen, and not on Nadia's page", True, "crossperson")
def y3():
    s = show([dict(OWEN, notes="wants pricing")], cards=[card("C3", "Lena Petrov", "Tidewater Physio", "lena@tide.ca", "wants a demo", by="Owen")]); r = row(s, "Lena")
    return f"{short(r)}; on Nadia: {'Lena' in view(s, 'nadia')}", r["status"].startswith("WAITING on Owen") and "Lena" not in view(s, "nadia")
@case("Y4", "Nothing goes from hello", "Attack A-V", "Every draft is from Owen or Nadia, with hello on cc", True)
def y4():
    s = show([OWEN, NADIA]); rs = [r for r in s["res"]["drafts"] if r["body"]]; return str([(r["sender"], r["cc"]) for r in rs]), all(r["sender"] in ("Owen", "Nadia") and r["cc"] for r in rs)
@case("Y5", "Erin's page has no drafts to send", "Attack A-V", "No Copy or Open in mail buttons on Erin's page", True)
def y5():
    s = show([OWEN, NADIA]); v = view(s, "erin"); return f"copy: {'class=' + chr(39) + 'act copy' in v}; mailto: {'mailto:' in v}", "act copy" not in v and "mailto:" not in v
@case("Y6", "Erin's page order", "Attack A-V", "This run, Check, Flags, Ready for follow-up, Excluded, Look up, in that order")
def y6():
    s = show([OWEN, NADIA]); v = view(s, "erin"); marks = ["to check", "This run", "Check (", "Flags (", "Ready for follow-up", "Excluded, no email", "Look up anyone"]; pos = [v.find(m) for m in marks]; return str(dict(zip(marks, pos))), min(pos) >= 0 and pos == sorted(pos)
@case("Y7", "A flag tells Erin who, why and what next", "Attack A-V", "Owner, reason and an Action line")
def y7():
    s = show([dict(OWEN, notes="wants pricing")], cards=[card("C3", "Lena Petrov", "Tidewater Physio", "lena@tide.ca", "wants a demo", by="Owen")]); v = view(s, "erin"); part = v[v.index("Flags ("):v.index("Ready for follow-up")]
    return re.sub(r"<[^>]+>", " ", part)[:260], "Lena Petrov" in part and "Owen · Needs confirmation" in part and "Action:" in part
@case("Y8", "A line the tool can't place", "Attack A-V", "Shows the line's ID, Owen, Identity unclear, and an Action")
def y8():
    s = show([OWEN], lines=["Red van chiro, numbers in writing"]); v = view(s, "erin"); part = v[v.index("Flags ("):v.index("Ready for follow-up")]; return re.sub(r"<[^>]+>", " ", part)[:260], "L0" in part and "Identity unclear" in part and "Action:" in part
if __name__ == "__main__": main()
