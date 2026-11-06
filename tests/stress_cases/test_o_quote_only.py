"""O: asked for a price and nothing else."""
from _harness import *
@case("O1", "'just a quote, no demo, no newsletter'", "Attack A-V", "Price only: no links, flagged for Erin", True)
def o1():
    s = show([scan("S1", "Oli", "Fox", "Fox Clinic", "o@f.ca", note="just a quote, no demo, no newsletter")]); r = row(s, "Oli"); return r["body"], r["next_step"] == "pricing" and "$34" in r["body"] and not re.search(r"\[|http", r["body"])
@case("O2", "Quote only, N flag", "Consent", "Held: no draft", True, "consent")
def o2():
    s = show([scan("S1", "Oli", "Fox", "Fox Clinic", "o@f.ca", "N", note="just a quote, no newsletter")]); return no_draft(s, "Oli")
@case("O3", "No marketing, on a paid system at two clinics, asked for info", "Attack A-V", "One-pager only: no demo link added", True)
def o3():
    s = show([scan("S1", "Oli", "Fox", "Fox Clinic", "o@f.ca", note="2 clinics on Clinivo, send info, no marketing")], settings=dict(one_pager="https://x/one", demo_link="https://x/demo")); r = row(s, "Oli"); return r["body"], "x/demo" not in r["body"]
if __name__ == "__main__": main()
