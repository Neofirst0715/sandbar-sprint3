"""H: language comes from the conversation; never from a card or a name."""
from _harness import *
@case("H1", "French card, Owen says they spoke English", "Attack A-V", "English, from Owen")
def h1():
    s = show([scan("S1", "Luc", "Roy", "Clinique Roy", "l@r.ca", note="")], cards=[card("C1", "Luc Roy", "Clinique Roy", "l@r.ca", "Propriétaire. Contrat à renouveler")], voice=[("Luc Roy at Clinique Roy, we talked in English, wants a demo", "2026-10-20 11:00")]); r = row(s, "Luc")
    return short(r), r["language"] == "English" and r["sender"] == "Owen"
@case("H2", "English card, note 'Nadia a parlé avec lui en français, démo fin d'année'", "Attack A-V", "French, from Nadia, demo")
def h2():
    s = show([scan("S1", "Ian", "Cole", "Cole Clinic", "i@c.ca", note="Nadia a parlé avec lui en français, démo fin d'année")], cards=[card("C1", "Ian Cole", "Cole Clinic", "i@c.ca", "owner")]); r = row(s, "Ian")
    return short(r), r["language"] == "French" and r["sender"] == "Nadia" and r["next_step"] == "demo"
@case("H3", "French name in an English note", "Attack A-V", "English")
def h3():
    s = show([scan("S1", "François", "Côté", "Cote Clinic", "f@c.ca", note="wants a demo")]); r = row(s, "Fran"); return short(r), r["language"] == "English"
@case("H4", "French note with English business words, from Nadia", "Attack A-V", "French, from Nadia")
def h4():
    s = show([scan("S1", "Ana", "Dubé", "Dube Clinic", "a@d.ca", note="", by="Nadia")], voice=[("c'est Nadia, Ana Dubé, Dube Clinic, en français, elle veut une demo pour le scheduling", "2026-10-20 11:00")]); r = row(s, "Ana")
    return short(r), r["language"] == "French" and r["sender"] == "Nadia"
@case("H5", "Both Owen and Nadia hold the promise", "Attack A-V", "Waits for them to decide; one sender")
def h5():
    s = show([scan("S1", "Sam", "Ivy", "Ivy Clinic", "s@i.ca", note="Nadia spoke to her too, demo", by="Nadia")], voice=[("Sam Ivy at Ivy Clinic wants a demo", "2026-10-20 11:00")]); r = row(s, "Sam")
    return short(r), r["status"].startswith("WAITING on Owen and Nadia")
@case("H6", "Notes say both French and English", "Attack A-V", "Not guessed silently: flagged")
def h6():
    s = show([scan("S1", "Sam", "Ivy", "Ivy Clinic", "s@i.ca", note="")], voice=[("Sam Ivy at Ivy Clinic spoke in English. Later on en français she asked for a demo.", "2026-10-20 11:00")]); r = row(s, "Sam")
    return f"{short(r)} {r['p']['flags']}", any("both in French and in English" in f for f in r["p"]["flags"])
@case("H7", "French conversation noted, but Owen holds the notes", "Attack A-V", "Waits for Owen and Nadia: French only goes out from Nadia")
def h7():
    s = show([scan("S1", "Sam", "Ivy", "Ivy Clinic", "s@i.ca", note="")], voice=[("Sam Ivy at Ivy Clinic, we spoke in French, wants a demo", "2026-10-20 11:00")]); r = row(s, "Sam")
    return short(r), r["status"].startswith("WAITING") or r["sender"] == "Nadia"
if __name__ == "__main__": main()
