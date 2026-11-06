"""The privacy firewall. Personal remarks stay out of everything that leaves this tool.

Three layers:
1. clean_clauses drops any clause with a personal or doubtful remark before the rules see the notes.
2. safe_detail is an allow-list: what's shown or exported is built only from facts the tool worked out
   (system, clinics, what was asked) and its own fixed sentences, never the note's own words.
3. scan_draft checks every finished draft, and audit_outputs checks every finished file.
Words on a list can't catch every kind of remark, which is why layer 2 doesn't copy notes at all."""
import csv, glob, os, re, unicodedata, zipfile

def _f(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()

PERSONAL = re.compile(r"\b(dad|father|mother|mom|mum|sister|brother|son|daughter|kid|kids|baby|pregnant|pregnancy|wife|husband|spouse|girlfriend|boyfriend|fiance|fiancee|"
    r"divorc\w*|separated|separation|marriage|affair|custody|widow\w*|funeral|dying|died|death|"
    r"sue|sued|suing|lawsuit|litigation|legal trouble|"
    r"surgery|operation|hospital\w*|chemo\w*|cancer|tumou?r|stroke|diagnos\w*|illness|terminal|mental health|depress\w*|anxiety|"
    r"bankrupt\w*|laid off|foreclos\w*|in debt|debts?|money troubles|"
    r"drinks|drinking|alcohol\w*|addict\w*|rehab facility|cried|crying|broke down|in tears|"
    r"dog|dogs|pics|photos|hockey|curling|brier|poor guy|funny|went to \w+ with|small world|knew \w+|bow tie|tall guy|lovely guy|nice guy|good guy|retiring|vacation)\b")
DOUBTFUL = re.compile(r"\b(trouble|troubles|struggling|upset|distracted|emotional|gossip|rumou?r|rude|hates?|hated|confidential|don'?t mention|do not mention|bring that up|keep this quiet|between us)\b")

SPLIT = re.compile(r"(?<=[.!?,;|/])\s+|\s+[|/-]\s+|\s+but\s+|\s+because\s+")

def is_personal(text): return bool(PERSONAL.search(_f(text)))
def is_doubtful(text): return bool(DOUBTFUL.search(_f(text)))

def clean_clauses(text):
    """(kept text, clauses dropped). Drops personal and doubtful clauses."""
    parts = [x for x in SPLIT.split(text or "") if x and x.strip()]
    kept = [x for x in parts if not is_personal(x) and not is_doubtful(x)]
    return " ".join(kept).strip(" ,;"), len(parts) - len(kept)

def personal_clauses(text):
    return [x.strip(" ,;.") for x in SPLIT.split(text or "") if x and x.strip() and (is_personal(x) or is_doubtful(x))]

def safe_detail(p, topic_sentence=""):
    """Only facts the tool worked out and its own fixed sentences. Never the words of the note."""
    bits = []
    if p.get("system"): bits.append(f"On {p['system']}")
    if p.get("locations"): bits.append(f"{p['locations']} clinic{'s' if p['locations'] != 1 else ''}")
    if p.get("first_batch") and p.get("next_step") not in (None, "thank-you note"): bits.append(f"Asked for: {p['next_step']}")
    if p.get("only_what_asked"): bits.append("Only what they asked for, no lists")
    if topic_sentence and not is_personal(topic_sentence) and not is_doubtful(topic_sentence): bits.append(topic_sentence)
    return "; ".join(bits)

def scan_draft(text, p=None):
    """Last check on a finished draft. Names and clinic names don't count. Returns the reason to stop, or ''."""
    t = _f(text)
    if p:
        for name in [p.get("clinic", ""), p.get("name", ""), p.get("first", ""), p.get("last", "")]:
            if name: t = t.replace(_f(name), " ")
        for raw in p.get("private_raw", []):
            if len(raw.split()) >= 3 and _f(raw) in t: return "contains a personal remark from the notes"
    m = PERSONAL.search(t)
    if m: return f"contains the word '{m.group(0)}'"
    m = DOUBTFUL.search(t)
    if m: return f"contains the word '{m.group(0)}', which may be personal"
    return ""

def audit_outputs(folder, raw_clauses):
    """Look for the notes' own personal clauses in every file written. Returns {file: first clause found}."""
    clauses = {_f(c) for c in raw_clauses if len(c.split()) >= 3}
    hits = {}
    for path in glob.glob(os.path.join(folder, "**", "*"), recursive=True):
        if not os.path.isfile(path): continue
        low = path.lower()
        try:
            if low.endswith(".xlsx"):
                z = zipfile.ZipFile(path); txt = " ".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist())
            elif low.endswith((".csv", ".html", ".txt", ".json")):
                txt = open(path, encoding="utf-8", errors="ignore").read()
            else: continue
        except Exception: continue
        t = _f(txt).replace("&#x27;", "'").replace("&apos;", "'")
        for c in clauses:
            if c in t:
                hits[os.path.relpath(path, folder)] = c; break
    return hits
