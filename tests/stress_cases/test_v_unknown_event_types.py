"""V: event types nobody planned for."""
from _harness import *
A = [scan("S1", "Val", "Oak", "Oak Clinic", "v@o.ca", note="demo")]
def go(e): return show(A, activity=[ev("E1", "2026-10-25 10:00", e, "Val Oak", "v@o.ca", "Oak Clinic")], today="2026-12-01")
@case("V1", "'webinar attended'", "Input", "Not counted; listed for Erin", True)
def v1():
    s = go("webinar attended"); return f"pile={person(s, 'Val')['pile']} issues={[x['reason'] for x in issues(s)]}", person(s, "Val")["pile"] == "never written to" and any("Unknown event" in x["reason"] for x in issues(s))
@case("V2", "'Demo Booked ' with odd case and a space", "Input", "Recognised")
def v2():
    s = go("Demo Booked "); return person(s, "Val")["pile"], person(s, "Val")["pile"] == "booked a demo"
@case("V3", "Blank event type", "Input", "Not counted; listed for Erin")
def v3():
    s = go(""); return str([x["reason"] for x in issues(s)]), any("Unknown event" in x["reason"] for x in issues(s))
@case("V4", "'unsubscribed' event", "Consent", "Treated as a removal: no draft", True, "consent")
def v4():
    return no_draft(go("unsubscribed"), "Val")
if __name__ == "__main__": main()
