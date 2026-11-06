"""I: other organisers' column names."""
from _harness import *
def file_show(rows):
    def raw(d):
        with open(d + "/export.csv", "w", newline="", encoding="utf-8") as f: csv.writer(f).writerows(rows)
    return show(raw=raw)
def good(s, name="Ida"):
    r = row(s, name); return short(r), bool(r) and r["next_step"] == "demo" and r["to"] == "i@a.ca" and r["clinic"] == "Ash Clinic"
SETS = {"I1": ["Telephone", "Given Name", "Surname", "Practice Name", "E-mail Address", "Share With Exhibitors", "Notes"], "I2": ["first_name", "last_name", "phone", "company", "email", "share", "notes"], "I3": ["FIRST NAME", "LAST NAME", "PHONE NUMBER", "ORGANIZATION", "EMAIL ADDRESS", "CONSENT", "COMMENTS"]}
VAL = {"Telephone": "506", "PHONE NUMBER": "506", "phone": "506"}
for cid, hdr in SETS.items():
    def mk(hdr=hdr):
        def f():
            vals = {"given": "Ida", "first": "Ida", "surname": "Ash", "last": "Ash", "practice": "Ash Clinic", "company": "Ash Clinic", "organization": "Ash Clinic", "mail": "i@a.ca", "share": "Y", "consent": "Y", "note": "wants a demo", "comment": "wants a demo", "phone": "506"}
            row_ = [next((v for k, v in vals.items() if k in h.lower().replace("-", "")), "506" if "tele" in h.lower() else "") for h in hdr]
            return good(file_show([hdr, row_]))
        return f
    case(cid, "Headers: " + ", ".join(hdr), "Input", "Read correctly, whatever the order or case", True)(mk())
for cid, h in [("I4", ["Attendee Name", "Organisation", "Email Address", "Phone Number", "Share", "Notes"]), ("I5", ["Contact Name", "Practice Name", "E-mail Address", "Telephone", "Consent", "Comments"]), ("I6", ["Full Name", "Company", "Email", "Phone", "Share", "Notes"])]:
    def mk2(h=h):
        return lambda: good(file_show([h, ["Ida Ash", "Ash Clinic", "i@a.ca", "5", "Y", "wants a demo"]]))
    case(cid, "One name column: " + h[0], "Input", "Name split safely and read correctly", True)(mk2())
@case("I7", "Duplicate header and a blank column", "Input", "First column used; reported to Erin")
def i7():
    s = file_show([["First Name", "First Name", "Last Name", "Company", "Email", "Share", "Notes", ""], ["Ida", "Wrong", "Ash", "Ash Clinic", "i@a.ca", "Y", "wants a demo", "x"]])
    r = row(s, "Ida"); return f"{short(r)} issues={[x['reason'] for x in issues(s)]}", bool(r) and any("appears twice" in x["reason"] for x in issues(s))
@case("I8", "Only one name in the one name column", "Input", "Kept as written and flagged to check")
def i8():
    s = file_show([["Attendee Name", "Company", "Email", "Share", "Notes"], ["Ash", "Ash Clinic", "i@a.ca", "Y", "wants a demo"]]); p = person(s, "Ash"); return str(p["flags"]), any("Only one name" in f for f in p["flags"])
@case("I9", "Scan file with columns it can't recognise", "Input", "Not lost silently: named on Erin's list", True)
def i9():
    s = None
    def raw(d):
        with open(d + "/mystery.csv", "w", newline="") as f: csv.writer(f).writerows([["alpha", "beta"], ["1", "2"]])
    s = show(TWO_DAYS, raw=raw); return str([x["reason"] for x in issues(s)]), any(x["file"] == "mystery.csv" for x in issues(s))
if __name__ == "__main__": main()
