"""S: text that isn't an address."""
from _harness import *
for i, em in enumerate(["N/A", "NA", "null", "None", "", "   ", "call him", "jean.example.com", "a@b", "two@a.ca, three@a.ca", "jean@example..com", "Jean <jean@example.com>"], 1):
    def mk(em=em):
        def f():
            s = show([scan("S1", "Jean", "Lev", "Lev Clinic", em, note="wants a demo", phone="506-555-0100")]); r = row(s, "Jean"); return short(r), not r["body"] and not r["status"].startswith("READY")
        return f
    case(f"S{i}", f"Email = {em!r}", "Attack A-V", "No draft, no READY; call reminder", True, "invalidemail")(mk())
for i, em in enumerate(["jean@example.com", " jean@example.com ", "jean＠example.com", "JEAN@EXAMPLE.COM", "mailto:jean@example.com"], 13):
    def mk2(em=em):
        def f():
            s = show([scan("S1", "Jean", "Lev", "Lev Clinic", em, note="wants a demo")]); r = row(s, "Jean"); return short(r), r["to"] == "jean@example.com" and bool(r["body"])
        return f
    case(f"S{i}", f"Email = {em!r}", "Attack A-V", "Normal form jean@example.com, draft offered")(mk2())
if __name__ == "__main__": main()
