"""K: one person, several records."""
from _harness import *
@case("K1", "Same person scanned twice", "Attack A-V", "One person, one draft", True, "duplicate")
def k1():
    s = show([scan("S1", "Kim", "Birch", "Birch Clinic", "k@b.ca", note="demo"), scan("S2", "Kim", "Birch", "Birch Clinic", "k@b.ca", note="demo")]); n = sum(1 for r in s["res"]["drafts"] if "Kim" in r["name"]); return f"{n} row", n == 1
@case("K2", "Scan and card, nickname and full name, same clinic", "Attack A-V", "One person")
def k2():
    s = show([scan("S1", "Jennifer", "Birch", "Birch Clinic", "jen@b.ca", note="")], cards=[card("C1", "Jen Birch", "Birch Clinic", "jen@b.ca", "demo")]); n = sum(1 for r in s["res"]["drafts"] if "Birch" in r["name"]); return f"{n} row", n == 1
@case("K3", "Same file dropped twice under two names", "Attack A-V", "No double counting", True, "duplicate")
def k3():
    def raw(d):
        import shutil; shutil.copy(d + "/badge-scans.csv", d + "/badge-scans copy.csv")
    s = show([scan("S1", "Kim", "Birch", "Birch Clinic", "k@b.ca", note="demo")], raw=raw); n = sum(1 for r in s["res"]["drafts"] if "Kim" in r["name"]); return f"{n} row", n == 1
if __name__ == "__main__": main()
