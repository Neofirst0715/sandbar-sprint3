#!/usr/bin/env python3
"""Sandbar after-show tool: joins a show's files into one row per person.

Usage: python3 sandbar.py <show_folder> <output_folder> [--state do_not_email.csv]

Standard library only. Sends nothing. No names from any particular show live in
this file: every rule works from the files it is given.
"""
import argparse, csv, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import defaultdict
from datetime import datetime, timedelta
from difflib import SequenceMatcher

# ---------- text helpers ----------
def fold(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()

# ---------- contact details and dates: one way of reading each ----------
NOT_AN_EMAIL = {"", "n/a", "na", "n.a.", "null", "none", "nil", "-", "--", "unknown", "tbd", "no email", "noemail", "not provided"}
def soft_email(raw):
    """Normal form only: full-width characters, spaces and case. Placeholder text becomes empty."""
    e = unicodedata.normalize("NFKC", str(raw or "")).replace("\u200b", "").strip().lower()
    e = re.sub(r"^mailto:", "", e)
    return "" if e in NOT_AN_EMAIL else e
def valid_email(e):
    return bool(re.fullmatch(r"[^@\s,;<>()\[\]]+@[^@\s,;<>()\[\]]+\.[a-z0-9-]{2,}", e or "")) and ".." not in e
def clean_email(raw):
    """(address, what was wrong). Never guesses: anything that isn't plainly an address becomes empty."""
    e = soft_email(raw)
    if valid_email(e): return e, ""
    return "", (str(raw or "").strip() if e else "")
def clean_phone(raw):
    p = unicodedata.normalize("NFKC", str(raw or "")).strip()
    return "" if p.lower() in NOT_AN_EMAIL else p

def parse_ts(raw):
    """(datetime, has a time) or None. Times are read as written, in the show's local time. An offset in the text is dropped,
    not converted, because the exports don't say which zone the rest is in. Day and month that could swap are not guessed."""
    s = unicodedata.normalize("NFKC", str(raw or "")).strip()
    if not s: return None
    iso = re.sub(r"Z$", "", s)
    try:
        d = datetime.fromisoformat(iso)
        return d.replace(tzinfo=None), bool(re.search(r"\d:\d", s))
    except ValueError: pass
    for fmt, has_time in [("%Y/%m/%d %H:%M", True), ("%Y/%m/%d", False), ("%b %d %Y %H:%M", True), ("%b %d, %Y %H:%M", True), ("%B %d %Y %H:%M", True), ("%B %d, %Y %H:%M", True), ("%b %d %Y", False), ("%b %d, %Y", False), ("%B %d %Y", False), ("%B %d, %Y", False)]:
        try: return datetime.strptime(s, fmt), has_time
        except ValueError: pass
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:[ T](\d{1,2}):(\d{2}))?", s)
    if m:
        a, b, y = int(m[1]), int(m[2]), int(m[3])
        if (a > 12) == (b > 12): return None  # could be either way round, or nonsense
        day, mon = (a, b) if a > 12 else (b, a)
        try: return datetime(y, mon, day, int(m[4] or 0), int(m[5] or 0)), bool(m[4])
        except ValueError: return None
    return None

def words(s):
    return re.findall(r"[a-z0-9]+", fold(s).replace("'", "").replace("’", ""))

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

NICK = [
    {"steve", "stephen", "steven"}, {"jen", "jenny", "jennifer"}, {"raj", "rajesh"},
    {"peggy", "margaret", "maggie", "meg"}, {"gord", "gordon"}, {"dan", "danny", "daniel"},
    {"dave", "david"}, {"bob", "rob", "robert", "bobby"},
    {"bill", "will", "william", "liam"}, {"jim", "james", "jimmy"}, {"tom", "thomas"},
    {"pat", "patrick", "patricia"}, {"liz", "beth", "elizabeth"}, {"kate", "katie", "kathleen", "katherine"},
    {"chris", "christopher", "christine"}, {"matt", "matthew"}, {"nick", "nicholas"},
    {"sue", "susan"}, {"ben", "benjamin"}, {"sam", "samuel", "samantha"}, {"alex", "alexis", "alexander"},
    {"stan", "stanislas", "stanley"}, {"bernie", "bernadette", "bernard"}, {"rick", "rich", "richard", "dick"}, {"tim", "timothy"}, {"sandy", "sandra"}, {"cathy", "kathy", "catherine", "katherine", "kate", "katie", "kathleen"}, {"ken", "kenneth"}, {"ron", "ronald"}, {"greg", "gregory"}, {"jeff", "jeffrey"}, {"steph", "stephanie"}, {"nat", "natalie", "nathalie"}, {"deb", "debbie", "deborah"}, {"gerry", "gerald"}, {"doug", "douglas"}, {"vic", "victor"}, {"remy", "remi"}, {"marie", "mary"}, {"bev", "beverly", "beverley"}, {"mike", "michael"}, {"andy", "andrew", "andrea"}, {"tony", "anthony"}, {"joe", "joseph"}, {"marc", "mark"},
]
def first_ok(a, b):
    """Could these be the same first name? Handles initials, nicknames, phone spelling."""
    a, b = fold(a).strip(". "), fold(b).strip(". ")
    if "." in a: a = a[0]
    if "." in b: b = b[0]
    if not a or not b: return True
    if len(a) == 1 or len(b) == 1: return a[0] == b[0]
    if a == b: return True
    if any(a in g and b in g for g in NICK if not {a, b} <= {"will", "liam"}): return True
    if a.replace("-", " ") == b.replace("-", " "): return True
    return min(len(a), len(b)) >= 4 and similar(a, b) >= 0.88

TITLES = {"dr", "mr", "mrs", "ms", "pt", "dc", "dpt", "rmt", "pht", "phd", "md", "r", "ac", "ot", "bsc"}
def split_name(raw):
    """Drops titles and credentials, keeps initials and two-part first names."""
    head = (raw or "").split(",")[0]
    toks = [t for t in re.split(r"\s+", fold(head).replace("'", "").replace("’", "")) if t]
    toks = [t.strip(".") for t in toks if t.strip(".") not in TITLES]
    if not toks: return "", ""
    if len(toks) == 1: return toks[0], ""
    return " ".join(toks[:-1]), toks[-1]

GENERIC_CLINIC = set("""physio physiotherapy rehab rehabilitation massage therapy therapeutic clinic clinics centre center
 health collective wellness sports sport group and the of inc ltd pht masso massotherapie massotherapeute acupuncture chiropractic chiro readaptation spine""".split())
def clinic_key(s):
    return [w for w in words(s) if w not in GENERIC_CLINIC]
def same_clinic(a, b):
    ka, kb = clinic_key(a), clinic_key(b)
    if not ka or not kb: return False
    return ka == kb or (len(ka) == len(kb) and all(similar(x, y) >= 0.85 for x, y in zip(ka, kb)))

def digits(s):
    d = re.sub(r"\D", "", (s or "").split("x")[0])
    return d[-10:] if len(d) >= 10 else ""

def transposed(a, b):
    """True if a and b differ only by two swapped neighbouring letters."""
    if len(a) != len(b) or a == b: return False
    diff = [i for i in range(len(a)) if a[i] != b[i]]
    return len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]

# ---------- reading files ----------
COLUMN_HINTS = {  # field -> keywords, most specific first. Order of fields matters.
    "scan_id": ["scan_id", "scan id", "lead id", "record id", "badge id", "id"],
    "scanned_at": ["scanned_at", "scanned at", "scan time", "capture time", "date_time", "timestamp", "date", "time"],
    "scanned_by": ["scanned_by", "scanned by", "captured by", "scanner", "collected by", "device", "user"],
    "company": ["company", "organization", "organisation", "employer", "clinic", "business", "practice", "facility"],
    "first": ["first_name", "first name", "firstname", "given name", "fname", "prenom"],
    "last": ["last_name", "last name", "lastname", "surname", "family name", "lname", "nom de famille"],
    "full": ["full name", "full_name", "attendee name", "contact name", "name", "nom"],
    "title": ["job title", "job_title", "title", "position", "role"],
    "email": ["email", "e-mail", "courriel"],
    "phone": ["phone", "mobile", "cell", "telephone"],
    "city": ["city", "town", "ville"],
    "province": ["province", "state", "region"],
    "share": ["share", "opt in", "optin", "opted", "consent", "permission", "contactable", "marketing", "exhibitor"],
    "rating": ["rating", "star", "lead score", "score", "grade", "qualif"],
    "notes": ["notes", "note", "comment", "remarks"],
}
def detect_columns(headers):
    """Map our fields to whatever this export calls them. Returns (mapping, unmapped headers)."""
    mapping, used = {}, set()
    norm = {h: fold(h).replace("-", " ") for h in headers}
    for field, hints in COLUMN_HINTS.items():
        for hint in hints:
            hit = next((h for h in headers if h not in used and
                        (norm[h] == hint.replace("-", " ") or
                         (len(hint) > 3 and hint.replace("-", " ") in norm[h]))), None)
            if hit:
                mapping[field] = hit; used.add(hit); break
    return mapping, [h for h in headers if h not in used]

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def find_inputs(folder):
    """Finds the show's files, including inside one folder someone dragged in whole."""
    found = {"scans": None, "notes": None, "activity": None}
    paths = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        paths += [os.path.join(root, f) for f in sorted(files) if not f.startswith(".")]
    for p in paths:
        fn = os.path.basename(p)
        if fn.lower().endswith(".json"):
            if fn.lower() != "settings.json" and not fn.lower().startswith("settings."): found["notes"] = p
        elif fn.lower().endswith(".csv"):
            head = fold(open(p, encoding="utf-8-sig", errors="replace").readline())
            if "event" in head and ("channel" in head or "detail" in head):
                found["activity"] = p
            elif "recount" in fn.lower() or "day30" in head:
                continue
            elif "email" in head or "mail" in head:
                found["scans"] = p
    return found

def yes_no(v):
    v = fold(v)
    if v in {"y", "yes", "true", "1", "oui", "opted in", "opt in"}: return "Y"
    if v in {"n", "no", "false", "0", "non", "opted out", "opt out", "opt-out", "declined", "do not share", "don't share", "no share"}: return "N"
    return ""

def load_scans(path, warnings):
    if not path:
        warnings.append("No scan export found: running from cards, voice notes and the list only."); return []
    rows = read_csv(path)
    if not rows: return []
    cols, unmapped = detect_columns(list(rows[0].keys()))
    for need in ["email", "company"]:
        if need not in cols: warnings.append(f"Scan export: could not find a '{need}' column.")
    if "first" not in cols and "full" not in cols: warnings.append("Scan export: could not find a name column.")
    if "share" not in cols: warnings.append("Scan export: no share/consent column found. Scan-only people are held until someone checks.")
    if unmapped: warnings.append("Scan export columns not used: " + ", ".join(unmapped))
    warnings.append("COLUMN CHECK (read this first): " + "; ".join(f"{k} = '{v}'" for k, v in cols.items()))
    out = []
    for i, r in enumerate(rows, 1):
        get = lambda k: (r.get(cols[k], "") or "").strip() if k in cols else ""
        name = f"{get('first')} {get('last')}".strip() or get("full")
        out.append(dict(id=get("scan_id") or f"row{i}", kind="scan", name=name.title() if name.isupper() else name,
                        title=get("title"), clinic=get("company"), email=clean_email(get("email"))[0], bad_email=clean_email(get("email"))[1], phone=clean_phone(get("phone")),
                        city=get("city"), share=yes_no(get("share")), rating=get("rating").upper()[:1], text=get("notes"),
                        by="Nadia" if "nadia" in fold(get("scanned_by")) else "Owen" if "owen" in fold(get("scanned_by")) else get("scanned_by"),
                        at=get("scanned_at")))
    return out

MAX_NOTE = 20000  # one note longer than this is cut, and Erin is told
def load_notes(path, warnings, issues=None):
    issues = issues if issues is not None else []
    if not path:
        warnings.append("No booth notes file found: running from scans only."); return [], [], []
    try:
        d = json.load(open(path, encoding="utf-8-sig"))
    except Exception as ex:
        issues.append(dict(file=os.path.basename(path), record="whole file", reason=f"Could not read it: {str(ex)[:100]}", review="yes"))
        warnings.append("Booth notes file could not be read: running from scans only."); return [], [], []
    def rows(key, sub=None):
        got = (d.get(key) or {}).get(sub) if sub else d.get(key)
        out = []
        for i, x in enumerate(got or [], 1):
            if isinstance(x, dict): out.append({k: ("" if v is None else v) for k, v in x.items()})
            else: issues.append(dict(file=os.path.basename(path), record=f"{sub or key} item {i}", reason="Empty or broken record, skipped", review="yes"))
        return out
    def trim(text, rec):
        text = str(text or "")
        if len(text) > MAX_NOTE:
            issues.append(dict(file=os.path.basename(path), record=rec, reason=f"Note is {len(text)} characters long. Only the first {MAX_NOTE} were read.", review="yes"))
            return text[:MAX_NOTE]
        return text
    cards = []
    for c in rows("cards"):
        em, bad = clean_email(c.get("email"))
        cards.append(dict(id=c.get("card_id", ""), kind="card", name=c.get("name", ""), title=c.get("title", ""), clinic=c.get("clinic", ""),
                  email=em, bad_email=bad, phone=clean_phone(c.get("phone")), city="", share="", rating="",
                  text=trim(c.get("back_of_card", ""), c.get("card_id", "card")), by=c.get("collected_by", ""), at=c.get("typed_on", "")))
    voices = []
    for v in rows("voice_notes"):
        t = trim(v.get("transcript", ""), v.get("note_id", "voice note"))
        voices.append(dict(id=v.get("note_id", ""), text=t, at=v.get("recorded_at", ""),
                   by=v.get("recorded_by", v.get("speaker", "Nadia" if re.match(r"\W*(c'est |it's |this is )?nadia\b", fold(t)) else "Owen"))))
    lines = [dict(id=l.get("line_id", ""), text=trim(l.get("text", ""), l.get("line_id", "list line"))) for l in rows("owen_list", "lines")]
    for label, val in [("cards", cards), ("voice notes", voices), ("Owen's list", lines)]:
        if not val: warnings.append(f"Booth notes: no {label} in this file. Running without them.")
    return cards, voices, lines

EVENT_FIELDS = "event_id date_time event channel name email clinic detail".split()
REVOKE_EVENTS = {"consent withdrawn", "unsubscribed", "unsubscribe", "opted out", "opt out", "removal requested", "do not contact"}
KNOWN_EVENTS = {"email sent", "email bounced", "reply received", "demo booked", "trial started", "demo cancelled", "demo canceled", "trial cancelled", "trial canceled"} | REVOKE_EVENTS
def load_activity(path, warnings, issues=None):
    issues = issues if issues is not None else []
    if not path:
        warnings.append("No after-show activity file: the four piles can't be counted yet."); return []
    out, seen = [], set()
    for i, r in enumerate(read_csv(path), 2):
        a = {k: str(r.get(k) or "").strip() for k in EVENT_FIELDS}
        a["event"] = a["event"].lower(); a["email"] = soft_email(a["email"]); a["row"] = a["event_id"] or f"row {i}"
        ts = parse_ts(a["date_time"]); stamp = ts[0].strftime("%Y-%m-%d %H:%M") if ts else a["date_time"]
        who = a["email"] or (fold(a["name"]) + "|" + fold(a["clinic"]))
        # The same event from two exports is one event. Different days for one person are different events.
        dup = (a["event"], who, stamp)
        if dup in seen: continue
        seen.add(dup)
        if a["event"] not in KNOWN_EVENTS:
            issues.append(dict(file=os.path.basename(path), record=a["row"], reason=f"Unknown event type '{a['event'] or '(blank)'}': not counted", review="yes"))
        out.append(a)
    return out

# ---------- joining records into people ----------
def domain_key(email):
    d = email.split("@")[-1].split(".")[0].replace("-", "") if "@" in email else ""
    return "" if d in ("example", "gmail", "hotmail", "outlook", "yahoo", "icloud") else d

def lasts_match(a, b):
    if not a or not b: return False
    if a == b or similar(a, b) >= 0.88: return True
    pa, pb = set(a.split("-")), set(b.split("-"))
    return bool(pa & pb)

def same_person(a, b):
    if a["email"] and a["email"] == b["email"] and not re.match(r"(info|office|frontdesk|front\.desk|hello|admin|reception)@", a["email"]):
        return True
    fa, la = split_name(a["name"]); fb, lb = split_name(b["name"])
    if not la or not lb or not lasts_match(la, lb): return False
    same_phone = bool(digits(a["phone"])) and digits(a["phone"]) == digits(b["phone"])
    same_dom = bool(domain_key(a["email"])) and domain_key(a["email"]) == domain_key(b["email"])
    if same_clinic(a["clinic"], b["clinic"]) or same_dom:
        return first_ok(fa, fb) or same_phone
    # same full name and phone, clinic written differently ("KV Massage")
    return first_ok(fa, fb) and same_phone

def cluster(records):
    people = []
    for r in records:
        hits = [p for p in people if any(same_person(r, x) for x in p["records"])]
        if not hits:
            people.append({"records": [r], "notes": []}); continue
        hits[0]["records"].append(r)
        for extra in hits[1:]:
            hits[0]["records"] += extra["records"]; people.remove(extra)
    for p in people:
        scans = [x for x in p["records"] if x["kind"] == "scan"]
        best = scans[0] if scans else p["records"][0]
        p["name"] = best["name"]; p["clinic"] = best["clinic"]; p["city"] = next((x["city"] for x in scans if x["city"]), "")
        p["title"] = best["title"]
        p["first"], p["last"] = split_name(best["name"])
        p["firsts"] = {split_name(x["name"])[0] for x in p["records"]}
    return people

def token_hit(tok, text_tokens, cutoff=0.85):
    return any(t == tok or (len(tok) > 3 and len(t) > 2 and similar(t, tok) >= cutoff) for t in text_tokens)

COMMON_WORDS = set("will hope mark rose dawn sage lark grace faith joy may june bill rob pat art frank".split())
def mentions(person, tokens, unique_firsts=None):
    """Is this person named here? A first name counts only with support, or when it is rare and unique at this show."""
    firsts = [f for f in person["firsts"] if len(f) > 1]
    first_exact = False; first_hit = False
    for f in firsts:
        head = f.split()[0].split("-")[0] if "." not in f else f
        if " " in f and all(token_hit(x, tokens, 1) for x in f.split()): first_hit = first_exact = True
        for t in tokens:
            if t == head and len(t) > 1: first_hit = first_exact = True
            elif len(t) >= 3 and "." not in f and first_ok(t, head) and t not in ("the", "she", "her", "his"): first_hit = True
    last_hit = bool(person["last"]) and any(token_hit(x, tokens, 0.82) for x in person["last"].split("-"))
    if person["last"] and not last_hit and first_hit:  # "Tanya B"
        last_hit = any(t == person["last"][0] for t in tokens if len(t) == 1)
    ck = clinic_key(person["clinic"]); joined = "".join(tokens)
    clinic_hit = bool(ck) and (all(token_hit(w, tokens, 0.88) for w in ck) or "".join(ck) in joined)
    clinic_part = bool(ck) and token_hit(ck[0], tokens, 0.88) and len(ck[0]) > 3
    city_w = words(person["city"])
    city_hit = bool(city_w) and all(token_hit(w, tokens, 1) for w in city_w)
    if first_hit and last_hit: return 5
    if first_hit and (clinic_hit or clinic_part): return 5
    if last_hit and clinic_hit and person["last"] not in ck: return 4
    if first_hit and city_hit: return 3
    if unique_firsts is not None and first_hit:
        key = next((f.split()[0] for f in firsts), "")
        if key and unique_firsts.get(key, 0) == 1 and key not in COMMON_WORDS and len(key) >= 4: return 3
    return 0

def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

def first_counts(people):
    c = defaultdict(int)
    for p in people:
        for f in {x.split()[0] for x in p["firsts"] if x}: c[f] += 1
    return c

def possibly_real(p):
    notes = " ".join(r["text"] for r in p["records"] if r["kind"] == "scan")
    return any(r["kind"] == "card" or r["rating"] for r in p["records"]) or (notes.strip() and not re.search(NOT_TALKED, fold(notes)))

def split_by_person(sentence, people):
    """One sentence, two named people: each gets the words after their own name. None if that can't be done safely."""
    t = fold(sentence)
    if re.search(r"\b(both|each of them|the two of them|they all|they both|either of them)\b", t): return None
    spots = []
    for p in people:
        names = [fold(x) for x in p["firsts"] if len(x) > 1] + ([p["last"]] if p["last"] else [])
        hit = min((m.start() for n in names for m in [re.search(r"\b" + re.escape(n) + r"\b", t)] if m), default=None)
        if hit is None: return None
        spots.append((hit, p))
    spots.sort(key=lambda x: x[0])
    out = []
    for i, (pos, p) in enumerate(spots):
        end = spots[i + 1][0] if i + 1 < len(spots) else len(t)
        out.append((p, t[pos:end]))
    # "Jen and Ravi want a demo": the first person's words have no ask of their own
    if any(not classify_text(chunk) for _, chunk in out):
        between = [c for _, c in out if not classify_text(c)]
        if all(re.fullmatch(r"[\w\s.'-]{0,40}\b(and|&)\s*", c) or re.fullmatch(r"[\w\s.'-]{0,40},\s*", c) for c in between):
            return [(p, sentence) for _, p in spots]
        return None
    return out

def place_voice(people, voices, flags_general):
    """Attach each voice-note sentence to the person it is about."""
    uniq = first_counts(people)
    for v in voices:
        tokens = words(v["text"])
        scored = [(mentions(p, tokens, uniq), p) for p in people]
        if not any(sc for sc, _ in scored):
            there = [p for p in people if possibly_real(p) and clinic_key(p["clinic"]) and all(token_hit(w, tokens, 0.88) for w in clinic_key(p["clinic"]))]
            if len(there) == 1: scored = [(3 if p is there[0] else 0, p) for p in people]
        top = [(s, p) for s, p in scored if s > 0]
        if not top:
            if classify_text(v["text"]):
                flags_general.append(dict(source=v["id"], text=clean_text(v["text"]), reason="Voice note with an ask that matches nobody in the files."))
            continue
        best = max(s for s, _ in top)
        here = [p for s, p in top if s >= 3 and (s == best or s >= 5)]
        if not here: continue
        # Two people with the same name: use the clinic if the note names one. Otherwise don't guess.
        same = defaultdict(list)
        for p in here: same[fold(p["name"])].append(p)
        for nm, group in same.items():
            if len(group) > 1:
                named = [p for p in group if clinic_key(p["clinic"]) and all(token_hit(w, tokens, 0.88) for w in clinic_key(p["clinic"]))]
                if len(named) == 1:
                    here = [p for p in here if p not in group or p is named[0]]
                else:
                    here = [p for p in here if p not in group]
                    flags_general.append(dict(source=v["id"], text=clean_text(v["text"]), reason=f"Voice note names {group[0]['name']}, and two people have that name ({group[0]['clinic']}; {group[1]['clinic']}). Not given to either."))
        if not here: continue
        cur = None
        for sent in sentences(v["text"]):
            st = words(sent)
            named_here = [p for p in here if mentions(p, st, uniq) >= 3]
            if len(named_here) >= 2 and classify_text(sent):
                parts = split_by_person(sent, named_here)
                if parts is None:
                    flags_general.append(dict(source=v["id"], text=clean_text(sent), reason="One sentence asks for something and names " + " and ".join(p["name"] for p in named_here) + ". The tool can't tell who asked for what. Not given to either."))
                else:
                    for p, chunk in parts: p["notes"].append(dict(source=v["id"], kind="voice", text=chunk, by=v["by"], at=v.get("at", "")))
                cur = named_here[-1]
                continue
            for p in here:
                if mentions(p, st, uniq) or any(t == f.split()[0] for f in p["firsts"] if len(f) > 1 for t in st):
                    cur = p
            cur = cur or here[0]
            cur["notes"].append(dict(source=v["id"], kind="voice", text=sent, by=v["by"], at=v.get("at", "")))
        for p in here:
            if not any(n["source"] == v["id"] for n in p["notes"]):
                p["notes"].append(dict(source=v["id"], kind="voice", text="", by=v["by"], at=v.get("at", "")))

STOP = set("""the a an and or of to in on at for with from w her his she he it its i we you they them that this is was are be been so just really
 not up all too but about some still one two three four five six clinic clinics guy lady big send wants want said got have has had
 okay ok oh my me out there what they you know don bring mean people talked""".split())
def keyset(s):
    return {normalise_system_words(w) for w in words(s) if w not in STOP and len(w) > 2}
def normalise_system_words(w):
    return {"pics": "photos", "pic": "photos"}.get(w, w)

def place_list(people, lines, voices, flags_general):
    uniq = first_counts(people)
    def own_words(p):
        text = " ".join(n["text"] for n in p["notes"]) + " " + " ".join(r["text"] for r in p["records"]) + " " + p["city"]
        return keyset(re.sub(r"clean evo", "clinivo", re.sub(r"book stead", "bookstead", re.sub(r"pract? shift", "pracshift", fold(text)))))
    for l in lines:
        tokens = words(l["text"])
        surname_hits = [p for p in people if p["last"] and token_hit(p["last"], tokens, 1)]
        if surname_hits and re.search(r"\bdr\b", fold(l["text"])):
            docs = [p for p in surname_hits if any(re.search(r"\bdr\b|dpt|doctor|director", fold(r["name"] + " " + r["title"])) for r in p["records"])]
            if len(docs) == 1:
                docs[0]["notes"].append(dict(source=l["id"], kind="list", text=l["text"], by="Owen")); continue
        scored = sorted(((mentions(p, tokens, uniq), id(p), p) for p in people if possibly_real(p) or p["notes"] or mentions(p, tokens, uniq) >= 5), key=lambda x: -x[0])
        if scored and scored[0][0] >= 3 and (len(scored) < 2 or scored[1][0] < scored[0][0]):
            scored[0][2]["notes"].append(dict(source=l["id"], kind="list", text=l["text"], by="Owen")); continue
        # a clinic name alone, when one person with records is there
        at_clinic = [p for p in people if possibly_real(p) and clinic_key(p["clinic"]) and all(token_hit(w, tokens, 0.88) for w in clinic_key(p["clinic"]))]
        if len(at_clinic) == 1:
            at_clinic[0]["notes"].append(dict(source=l["id"], kind="list", text=l["text"], by="Owen")); continue
        # description lines: words shared with what this person's own notes say
        ks = keyset(l["text"]); ranked = sorted(((len(ks & own_words(p)), id(p), p) for p in people if p["notes"] or possibly_real(p)), key=lambda x: -x[0])
        if ranked and ranked[0][0] >= 2 and (len(ranked) < 2 or ranked[1][0] < ranked[0][0]):
            ranked[0][2]["notes"].append(dict(source=l["id"], kind="list", text=l["text"], by="Owen", guessed=True)); continue
        guess = next((p["name"] for sc, _, p in ranked if sc > 0), "")
        flags_general.append(dict(source=l["id"], text=clean_text(l["text"]), reason="List line the tool can't place." + (f" Best guess: {guess}." if guess else "")))

# ---------- what people said ----------
SYSTEMS = [("Clinivo", r"clini?vo|clean\s?evo"), ("Bookstead", r"book\s?stead|\bbs user\b"), ("Pracshift", r"pract?\s?shift")]
LEFT = r"(ditched|left|refugee|moved off|dropped|cancelled)"
def find_system(text):
    t = fold(text)
    for name, pat in SYSTEMS:
        m = re.search(pat, t)
        if not m: continue
        window = t[max(0, m.start() - 25): m.end() + 15]
        if re.search(LEFT, window): continue
        return name
    return ""

NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
def find_locations(text):
    t = fold(text)
    m = re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:\w+\s+)?(sites?|clinics?|locs?|locations?)\b", t)
    if m:
        return int(m.group(1)) if m.group(1).isdigit() else NUM[m.group(1)]
    if re.search(r"\b(solo|single clinic)\b", t): return 1
    return 0

WITHDRAW_ASK = re.compile(r"(?:(?<!still )\bno(?=\s+(?:demo|trial|pricing|quote)\b(?!\s+(?:from|sent|link|given|booked|after|back|yet from)))|\bcancel(?:led|ed)?(?: the)?|\bnot interested in(?: a| the)?|\bno longer (?:wants?|interested in)(?: a| the)?|\b(?:doesn'?t|don'?t|does not|do not|didn'?t) (?:want|need)(?: a| the)?|\bdo not send(?: a| the)?|\bdon'?t send(?: a| the)?|\bdrop(?:ped)? the|\bskip the)\s+(demo|trial|pricing|quote)\b")
def withdrawn_asks(text):
    """What this text says they no longer want."""
    t = fold(text); out = set()
    for sent in re.split(r"[.;!]", t):
        for m in WITHDRAW_ASK.finditer(sent): out.add({"quote": "pricing"}.get(m.group(1), m.group(1)))
        if re.search(r"changed (her|his|their|my) mind|decided against|called (it|that) off|no longer interested|not interested (any ?more|after all)", sent):
            for w, a in [("demo", "demo"), ("trial", "trial"), ("pricing", "pricing"), ("quote", "pricing")]:
                if re.search(r"\b" + w + r"\b", sent): out.add(a)
    return out

def classify_text(text):
    """Returns a list of (ask, tentative). Ask is demo / pricing / trial / call back / document / info."""
    t = fold(text)
    # Owen correcting himself: drop what he says he got wrong
    t = re.sub(r"[^.]*\b(but no|that'?s wrong|ignore what i typed)\b[,.]?", " ", t)
    asks = []
    if re.search(r"(didn'?t|did not) ask for anything|nothing to send|nothing there", t) and not re.search(r"\bdemo\b|pricing|trial", t):
        return []
    t = WITHDRAW_ASK.sub(" ", t)
    t2 = re.sub(r"\b(do not|don'?t|no need to) push (a |the )?(demo|trial)( now| yet)?|\bno (demo|trial) (yet|now|for now)\b|\b(not|doesn'?t want|does not want|don'?t want) (a |the )?(demo|trial)\b|doesn'?t want to (fiddle|try)[^.,]*|knows what we cost[^.,]*|numbers guy|get a number[^.,]*", " ", t)
    def add(ask, pat):
        for m in re.finditer(pat, t2):
            tail = t2[m.end(): m.end() + 2]
            asks.append((ask, "?" in tail))
    add("demo", r"\bdemo\b|walk (me|him|her|them|us) (thru|through)|show (me|her|him|them|us)\b(?! the owner)|see it\b|see the whole thing|wants? a look|book a look|screen share|take (me|him|her|them) through|sit down and")
    add("trial", r"\btrial\b|test drive|kick the tires|play with it|try it\b(?! with)?|wants to try|set (her|him|them) up")
    add("pricing", r"\bpricing\b|\$\$|\$ per|price per|\bquote\b|what it costs|what (it|you) cost|how much|cost per|\bnumbers\b|just the number")
    if re.search(r"\b(call|ring|phone) (me|her|him|them)\b.*\b(once|when|after|in (january|february|march|april|may|june|july|august|september|october|november|december))\b|\b(ring|phone|call) (me|her|him|them) in\b|\bcall (when|once|after)\b|\bcall (her |him |them |me )?(mid|around|early|late)\b|\b(reminder|remind \w+) to (call|phone|ring)\b|\b(phone|call) only\b|\bwe'?d (call|ring)\b|\b(ap|r)appeler\b|\bring (him|her|me)\b", t2):
        asks.append(("call back", False))
    if re.search(r"\bsoc ?2\b|security spec|(security|privacy|compliance)\s+(\w+\s+)?(doc|document|one.?pager|sheet|page|thing|policy|spec|overview|details|review|questionnaire|write.?up)", t2):
        asks.append(("document", False))
    elif re.search(r"send (me |her |him |them |some |the )*(info|brochure|one.?pager|stuff|flyer)|info for (the |his |her )?(owner|boss|partner)|wants? info\b|for (the |his |her )?owner|something (he|she|they) can (show|take)|something to read|brochure|one.?pager|\bflyer\b|\bleaflet\b|\bpamphlet\b", t2):
        asks.append(("info", False))
    # a call back beats a demo or trial mentioned in the same breath
    if any(a == "call back" for a, _ in asks) and re.search(r"not before|don'?t (send|push)|no emails?|phone only", t2):
        asks = [x for x in asks if x[0] in ("call back",)]
    return asks

import privacy as _privacy
def clean_text(text):
    """Drop clauses with personal remarks. Runs before anything is written out."""
    return _privacy.clean_clauses(text)[0]

NOT_TALKED = r"\b(draw|espresso|swag|didnt talk|didn'?t talk|didnt speak|didn'?t speak|no chat|no convo|comp|exhibitor|student|raffle|ballot|tote|prize|pens|just the coffee|coffee only|test|booth \d+|took a pen|saying hi|came by (the )?(booth )?again)\b"
WEAK = r"^(again|came back|said hi|again - said hi|popped by|back again)\b"
NON_BUYER_TITLE = r"(student|sales rep|account (executive|manager)|territory manager|exhibitor|event staff|marketing|vendor|supplier|organi[sz]er)"

def judge(p, activity_people=None):
    recs = p["records"]; scans = [r for r in recs if r["kind"] == "scan"]; cards = [r for r in recs if r["kind"] == "card"]
    voice = [n for n in p["notes"] if n["kind"] == "voice"]; lst = [n for n in p["notes"] if n["kind"] == "list"]
    flags = []
    # --- real conversation
    scan_notes = [r["text"] for r in scans if r["text"].strip()]
    excluded_note = any(re.search(NOT_TALKED, fold(n)) for n in scan_notes)
    strong_note = any(not re.search(NOT_TALKED, fold(n)) and not re.search(WEAK, fold(n)) for n in scan_notes)
    star = any(r["rating"] for r in scans)
    other = bool(cards or voice or lst)
    nonbuyer = any(re.search(NON_BUYER_TITLE, fold(r["title"])) for r in recs)
    competitor = any(re.fullmatch(r"(clinivo|bookstead|pracshift)", fold(r["clinic"])) for r in recs)
    if competitor or (nonbuyer and not (voice or lst)): real = False; why = "student, vendor, competitor or staff"
    elif other: real = True; why = "card, voice note or list"
    elif excluded_note: real = False; why = "scan note says no conversation"
    elif nonbuyer: real = False; why = "student, vendor or staff with no note"
    elif strong_note: real = True; why = "scan note"
    elif star: real = True; why = "star rating"
    else: real = False; why = "no record of a conversation"
    p["real"], p["real_why"] = real, why
    # --- what they use, how big
    sources = [("voice", n["text"]) for n in voice] + [("list", n["text"]) for n in lst] + \
              [("card", r["text"]) for r in cards] + [("scan", r["text"]) for r in scans]
    p["system"] = next((s for _, t in sources for s in [find_system(t)] if s), "")
    locs = [find_locations(t) for _, t in sources]
    locs = [x for x in locs if x]
    ratings = [r["rating"] for r in scans if r["rating"]]
    if locs: p["locations"] = max(locs)
    elif "A" in ratings: p["locations"] = 3
    elif "B" in ratings: p["locations"] = 2
    elif "C" in ratings: p["locations"] = 1
    else: p["locations"] = 0
    # --- what they asked for, best source first
    rank = {"voice": 0, "list": 1, "card": 2, "scan": 3}
    found = defaultdict(list)
    for src, text in sources:
        for ask, tentative in classify_text(text):
            found[src].append((ask, tentative))
    definite = [(src, a) for src in ["voice", "list", "card", "scan"] for a, t in found[src] if not t]
    # A clear "no longer wants it" outranks any older ask. A newer clear ask outranks an older "no".
    def when(src):
        recs_ = {"scan": [r["at"] for r in scans], "card": [r["at"] for r in cards], "voice": [n.get("at", "") for n in voice]}.get(src, [])
        got = [parse_ts(x) for x in recs_]; got = [g[0] for g in got if g]
        return max(got) if got else None
    gone = []
    for src, text in sources:
        for a in withdrawn_asks(text):
            w = when(src)
            if not any(x == a and x_src != src and when(x_src) and w and when(x_src) > w for x_src, x in definite):
                definite = [(x_src, x) for x_src, x in definite if x != a]
                if a not in gone:
                    gone.append(a); flags.append(f"For Owen: the notes say they no longer want the {a} ({src}). No {a} in the draft.")
    tentative = [(src, a) for src in ["voice", "list", "card", "scan"] for a, t in found[src] if t and a not in gone]
    PROMISE = ["demo", "pricing", "trial", "call back"]
    ask = None; ask_src = ""
    promise = [(s, a) for s, a in definite if a in PROMISE]
    if promise:
        top_rank = min(rank[s] for s, _ in promise)
        at_top = [a for s, a in promise if rank[s] == top_rank]
        ask = at_top[0]; ask_src = next(s for s, a in promise if rank[s] == top_rank)
        others = {a for _, a in promise} - {ask}
        if others:
            if ask_src == "voice":
                flags.append(f"Source conflict: went with the voice note ({ask}), the fullest record of the conversation; also saw {', '.join(sorted(others))}. Consent is checked separately.")
            else:
                flags.append(f"Sources disagree on what was asked: {ask} vs {', '.join(sorted(others))}. Owen to check.")
    doc = any(a == "document" for _, a in definite)
    info = any(a == "info" for _, a in definite)
    tent_other = sorted({a for _, a in tentative} - ({ask} if ask else set()))
    if tent_other and ask:
        p["aside"] = f"Maybe also: {', '.join(tent_other)} (they weren't sure)."
    elif tent_other and not ask:
        flags.append(f"Only a question mark on {', '.join(tent_other)}: treated as not asked. Owen to check.")
    # --- priority and next step
    if ask:
        p["priority"], p["next_step"], p["why"] = "hot", ask, f"Asked for {ask} ({ask_src})."
    else:
        warm = p["locations"] >= 2 or p["system"] in {"Clinivo", "Bookstead", "Pracshift"}
        p["priority"] = "warm" if warm else "cold"
        p["next_step"] = "send info" if info or doc else "thank-you note"
        bits = []
        if p["locations"] >= 2: bits.append(f"{p['locations']} clinics")
        if p["system"]: bits.append(f"on {p['system']}")
        p["why"] = (", ".join(bits) or "one clinic or unknown, no paid system") + \
                   ("; owes one specific document" if doc else "; asked for info" if info else "; nothing asked")
        if doc:
            flags.append("For Owen: owes one specific document, so it goes out with the promises. Check it exists; if not, Owen calls instead of pretending.")
    p["first_batch"] = bool(ask or doc)
    # --- who it comes from and where it goes
    alltext = " ".join(t for _, t in sources)
    # French only when the booth notes say the conversation was in French, never from a title or a card's layout
    spoken = " ".join(t for src, t in sources if src != "card")
    card_says = " ".join(t for src, t in sources if src == "card")
    said_english = bool(re.search(r"\b(in|spoke|speak|speaks|speaking|talked|talking|chatted|english only)\b[^.]{0,20}\benglish\b|\benglish\b[^.]{0,20}\b(conversation|only)\b", fold(spoken + " " + card_says)))
    ft = re.sub(r"[^.]*\benglish\b[^.]*", " ", fold(spoken))
    fr_spoken = bool(re.search(r"\bfrench\b|\bfrancais\b|\b(r|ap)appeler\b|\brenouvellement\b|\bcontrat\b", ft)) or bool(re.search(r"(parle|spoke|talked|chatted)[^.]{0,25}(french|francais)", fold(card_says)))
    p["french"] = fr_spoken and not said_english
    if fr_spoken and said_english:
        flags.append("Notes say this conversation was both in French and in English. Draft is in English. Check which.")
    def says_something(r):
        t = fold(r["text"]).strip()
        return bool(t) and not re.search(NOT_TALKED, t) and not re.search(WEAK, t) and "already talked" not in t and not re.search(r"already (w|with)\b", t)
    owen_voice = [n for n in voice if n.get("by") != "Nadia"]; nadia_voice = [n for n in voice if n.get("by") == "Nadia"]
    owen_said = bool(owen_voice or lst) or any(r["by"] == "Owen" and says_something(r) for r in recs)
    nadia_said = bool(nadia_voice) or any(r["by"] == "Nadia" and says_something(r) for r in recs)
    handed_to_nadia = bool(re.search(r"nadia should|nadia told|nadia just told", fold(alltext)))
    nadia_spoke = bool(re.search(r"nadia a parle|nadia (spoke|talked|chatted) (to|with) (him|her|them)(?! too)", fold(alltext)))
    if nadia_spoke and not (voice or lst): handed_to_nadia = True
    def holds_promise(who):
        recs_text = " ".join(r["text"] for r in recs if r["by"] == who)
        if who == "Owen": recs_text += " " + " ".join(n["text"] for n in owen_voice + lst)
        else: recs_text += " " + " ".join(n["text"] for n in nadia_voice)
        return any(not t and a in ("demo", "pricing", "trial", "call back", "document") for a, t in classify_text(recs_text))
    if handed_to_nadia: p["sender"] = "Nadia"
    elif ask or doc:
        o, n = holds_promise("Owen"), holds_promise("Nadia")
        p["sender"] = "Nadia" if n and not o else "Owen"
        if o and n: flags.append("For Owen and Nadia: both wrote down this promise. Decide who sends; only one of you should.")
    elif owen_said and nadia_said:
        p["sender"] = "Owen"
        flags.append("For Owen and Nadia: both have notes on this person. Decide who sends; only one of you should.")
    elif nadia_said: p["sender"] = "Nadia"
    else: p["sender"] = "Owen"
    only_scan = bool(scans) and not cards and not voice and not lst
    if p["french"] and p["sender"] != "Nadia":
        flags.append("For Owen and Nadia: the notes say this was in French, and French only goes out from Nadia. Decide who sends; only one of you should.")
    if only_scan and p["sender"] == "Nadia" and not nadia_spoke:
        flags.append("For Nadia: scanned on your phone, nothing else. Was this you?")
    badge = next((r["email"] for r in scans if r["email"]), "")
    card = next((r["email"] for r in cards if r["email"]), "")
    p["email"] = card or badge
    if card and badge and card != badge:
        cu, cd = card.split("@")[-2:] if "@" in card else (card, ""); bu, bd = badge.split("@")[-2:] if "@" in badge else (badge, "")
        if transposed(cd, bd) or transposed(cu, bu):
            p["email"] = badge
            flags.append(f"Card email looks mistyped ({card}): switched to badge email. Check it before sending.")
    p["all_emails"] = sorted({r["email"] for r in recs if r["email"]})
    p["phone"] = next((r["phone"] for r in recs if r["phone"]), "")
    p["bad_emails"] = sorted({r["bad_email"] for r in recs if r.get("bad_email")})
    if p["bad_emails"]:
        flags.append(f"Address isn't usable as written: {', '.join(p['bad_emails'])}. Not guessed." + (f" Using {p['email']}." if p["email"] else ""))
    # --- consent
    # Consent is a gate of its own. What someone asked for never opens it.
    n_flag = any(r["share"] == "N" for r in scans)
    unknown = bool(scans) and not any(r["share"] for r in scans) and not cards
    no_list = bool(re.search(r"(no|not|don'?t put her on any|do not put \w+ on any) mailing list|hates newsletters|no newsletter|no lists?\b|no marketing|not? (any )?marketing|do not (dare )?put \w+ on a marketing", fold(alltext)))
    customer = bool(re.search(r"existing customer|already a customer|current customer|already (on|using) (sandbar|us|our)|customer of ours|our customer", fold(alltext)))
    revoked = not (ask == "call back") and bool(re.search(r"withdr[ae]w\w*( her| his| their| my)? (consent|permission)|revoked? (consent|permission)|(do not|don'?t|stop) (email|emailing|contact|contacting) (her|him|them|me|us)\b|asked (us )?not to (email|contact)|take (her|him|them|me) off|remove (her|him|them|me) from|\bunsubscribed?\b", fold(alltext)))
    hold = None; p["legal_hold"] = False; p["revoked"] = revoked
    if n_flag:
        p["legal_hold"] = True
        asked = f" They asked for {ask} at the booth ({ask_src})." if ask else (" They owe a document." if doc else "")
        if cards:
            hold = f"Share flag N with a card: badge consent = N.{asked} A card or a request isn't permission, so no draft. Held until someone who knows the law decides."
        else:
            hold = f"Share flag N and no card: badge consent = N.{asked} A request isn't permission, so no draft. Held until someone who knows the law decides."
    if unknown and not hold: hold = "No consent value in the scan export: held until checked."
    if no_list:
        p["only_what_asked"] = True
        flags.append("Said no marketing or mailing lists: reply with what was asked only, never the newsletter. Erin checks this is a reply to their own request.")
    if customer and not hold: hold = "Existing customer: Owen phones instead of a sales email."
    if not hold and re.search(r"looking forward to our \w+ (call|meeting|chat)|already (in touch|talking|speaking) (with|to)", fold(alltext)):
        hold = "Already in touch with us: no draft. Owen checks."
    if revoked and not p["legal_hold"]:
        hold = "HIGH RISK: the notes say they withdrew permission or asked not to be contacted. No draft, for this and every show."
    p["hold"] = hold
    if not (p["name"] or "").strip() and not hold:
        p["hold"] = hold = "No name on this record. Erin checks it before anything goes out."
    elif len((p["name"] or "").split()) == 1:
        flags.append(f"Only one name on this record ('{p['name']}'). Check it.")
    p["contact_source"] = "asked at booth" if ask else "card handed over" if cards else "badge scan, not opted in" if n_flag else "badge scan, opted in" if scans else "notes only"
    if hold: flags.append(hold)
    p["guessed"] = [n["source"] for n in lst if n.get("guessed")]
    if p["guessed"]: flags.append(f"List line {p['guessed'][0]} placed by a guess. Owen to confirm.")
    # --- details safe to show
    p["booth_detail"] = " ".join(x for x in [clean_text(t) for _, t in sources if t] if x)  # internal: picks a fixed sentence, never exported
    p["private_raw"] = [c for _, t in sources for c in _privacy.personal_clauses(t)]
    p["flags"] = flags
    return p

# ---------- across shows: people who must never get email ----------
REMOVAL = r"(take me off|remove me|unsubscribe|stop emailing|stop contacting|off your list|do not (contact|email) me|don'?t (contact|email) me|no more emails|withdr[ae]w\w* (my )?(consent|permission)|opt(ing|ed)? (me )?out)"
def load_dne(path):
    return read_csv(path) if path and os.path.exists(path) else []
def _name_parts(p):
    out = [(p["first"], p["last"])]
    for r in p["records"]:
        f, l = split_name(r.get("name", ""))
        if (f, l) not in out: out.append((f, l))
    return out
def _clinic_close(a, b):
    if not a or not b: return False
    if same_clinic(a, b): return True
    ka, kb = "".join(clinic_key(a)), "".join(clinic_key(b))
    return bool(ka and kb) and similar(ka, kb) >= 0.8
def _last_overlap(a, b):
    pa, pb = set(re.split(r"[- ]", fold(a))), set(re.split(r"[- ]", fold(b)))
    return bool(pa & pb - {""})
def dne_check(p, dne):
    """Checks the do-not-email list in order: address, then name and clinic, then close name and close clinic, then 'might be'.
    Returns ('confirmed' or 'suspected', list row, why) or None. Same name alone is never enough to say confirmed."""
    for d in dne:
        e = soft_email(d.get("email"))
        if e and e in p["all_emails"]: return "confirmed", d, f"same address ({e})"
    suspect = None
    for d in dne:
        f, l = split_name(d.get("name", ""))
        if not l: continue
        for pf, pl in _name_parts(p):
            exact = l == pl and first_ok(f, pf)
            close = (similar(fold(f + " " + l), fold(pf + " " + pl)) >= 0.82 and similar(l, pl) >= 0.75) or (_last_overlap(l, pl) and first_ok(f, pf))
            clinic = _clinic_close(d.get("clinic", ""), p["clinic"])
            if exact and clinic: return "confirmed", d, "same name and clinic"
            swapped = bool(pf and pl) and fold(pf) == fold(l) and fold(pl) == fold(f)
            first_only = clinic and first_ok(f, pf) and len(fold(pf)) > 1 and bool(pl) and fold(pl)[0] == fold(l)[0]
            if (swapped or first_only) and not close and not suspect:
                suspect = ("suspected", d, f"name is close to {d.get('name')}" + ("; first and last swapped" if swapped else "") + ("; same clinic" if clinic else ""))
            if close and clinic: return "confirmed", d, f"very close name ({d.get('name')}) and same clinic"
            if (exact or close) and not suspect:
                same_dom = bool(domain_key(d.get("email", ""))) and any(domain_key(e) == domain_key(d.get("email", "")) for e in p["all_emails"])
                suspect = ("suspected", d, f"name matches {d.get('name')}" + ("; same email domain" if same_dom else f"; clinic differs (list says {d.get('clinic') or 'no clinic'})"))
    return suspect
def on_dne(p, dne):
    hit = dne_check(p, dne)
    return hit[1] if hit and hit[0] == "confirmed" else None

# ---------- 30 days after the show ----------
NOT_SHOW = r"(google|instagram|facebook|podcast|review site|a friend|a colleague|colleague|friend|referral|linkedin|search)"
def hear(detail):
    m = re.search(r"how did you hear about us:\s*(.*)$", detail, re.I)
    return m.group(1).strip() if m else ""

def in_window(raw, show_start, show_end):
    """Rule: an event counts from the start of the show to exactly 30 days after the end of the show, end included.
    Returns ('in'|'before'|'after'|'unreadable'|'no window', parsed time, note)."""
    ts = parse_ts(raw)
    if not ts: return "unreadable", None, ""
    if not show_start or not show_end: return "no window", ts[0], ""
    t, has_time = ts; deadline = show_end + timedelta(days=30)
    if has_time:
        return ("before" if t < show_start else "after" if t > deadline else "in"), t, ""
    d = t.date()
    if d < show_start.date(): return "before", t, ""
    if d > deadline.date(): return "after", t, ""
    note = "date with no time, on the day the window opens or closes: counted, check it" if d in (show_start.date(), deadline.date()) else ""
    return "in", t, note

def piles(people, activity, show_end, show_start=None, issues=None):
    issues = issues if issues is not None else []
    real = [p for p in people if p["real"]]
    bounced = {a["email"] for a in activity if a["event"] == "email bounced" and a["email"]}
    for p in real:
        p["sent"], p["sent_in_window"], p["pile_evidence"], p["pile"] = [], [], "", None
    def who(a):
        em = a.get("email") or ""
        for p in real:
            if em and em in p["all_emails"]: return p, "same email"
        f, l = split_name(a.get("name", ""))
        for p in real:
            if l and l == p["last"] and first_ok(f, p["first"]) and same_clinic(a.get("clinic", ""), p["clinic"]):
                return p, "same name and clinic"
            if l and l == p["last"] and same_clinic(a.get("clinic", ""), p["clinic"]):
                return p, "same surname and clinic"
        return None, ""
    def bad_date(a, what):
        issues.append(dict(file="after-show activity", record=a["row"], reason=f"Can't read the date '{a['date_time']}' on '{a['event']}': {what}", review="yes"))
    outcomes = defaultdict(list)
    review = []
    if activity and not (show_start and show_end):
        issues.append(dict(file="show files", record="whole show", reason="No readable scan or voice-note times, so the show's dates are unknown. Bookings and trials are not counted.", review="yes"))
    for a in activity:
        ev = a["event"]
        if ev == "email sent":
            p, _ = who(a)
            if not p or a["email"] in bounced: continue
            where, _t, note = in_window(a["date_time"], show_start, show_end)
            if where == "unreadable":
                if a["date_time"] or a.get("channel") != "already-sent list":
                    bad_date(a, "kept as written to so nobody gets a second email, but not counted in the piles")
                    p["sent"].append(f"date unreadable: {a['date_time']} {a['channel']}"); continue
                p["sent"].append(f"no date given {a['channel']}"); p["sent_in_window"].append(f"no date given {a['channel']}"); continue
            if where == "before":
                p["flags"].append(f"For Erin: email sent {a['date_time']}, before the show. Not counted."); continue
            p["sent"].append(f"{a['date_time'][:16]} {a['channel']}")
            if where == "in": p["sent_in_window"].append(f"{a['date_time'][:16]} {a['channel']}")
            elif where == "after": p["flags"].append(f"For Erin: email sent {a['date_time']}, after the 30-day window. Not counted in the piles.")
        elif ev == "reply received":
            if re.search(REMOVAL, fold(a["detail"])):
                review.append(dict(name=a["name"], email=a["email"], clinic=a["clinic"], date=a["date_time"][:10]))
        elif ev in REVOKE_EVENTS:
            review.append(dict(name=a["name"], email=a["email"], clinic=a["clinic"], date=a["date_time"][:10]))
        elif ev in ("demo cancelled", "demo canceled", "trial cancelled", "trial canceled"):
            p, _ = who(a)
            if p: p["flags"].append(f"For Erin: {ev} on {a['date_time'][:16]}. A booking by day 30 still counts in the piles (Nadia, Erin). Check it.")
        elif ev in ("demo booked", "trial started"):
            pile = "booked a demo" if ev == "demo booked" else "started a trial"
            where, _t, note = in_window(a["date_time"], show_start, show_end)
            if where == "unreadable":
                bad_date(a, "not counted"); p, _ = who(a)
                if p: p["flags"].append(f"For Erin: {ev}, but the date can't be read ('{a['date_time']}'). Not counted.")
                continue
            if where == "no window": continue
            if where == "before":
                p, _ = who(a)
                if p: p["flags"].append(f"For Erin: {ev} on {a['date_time'][:16]}, before the show. Not counted in the piles.")
                continue
            if where == "after":
                p, _ = who(a)
                if p: p["flags"].append(f"For Erin: {ev} on {a['date_time'][:16]}, after the 30-day window. Not counted in the piles.")
                continue
            p, how = who(a)
            source = hear(a["detail"])
            if not p:
                if re.search(NOT_SHOW, fold(source)) and not re.search(r"owen|nadia|expo|booth|show", fold(source)):
                    continue
                at_clinic = [x for x in real if same_clinic(a.get("clinic", ""), x["clinic"])]
                if not at_clinic: continue
                named = [x for x in at_clinic if x["first"] and re.search(rf"\b{re.escape(x['first'][:3])}", fold(a["detail"])) and x["last"] in fold(a["detail"])]
                wanted = "demo" if ev == "demo booked" else "trial"
                asked = [x for x in at_clinic if x["next_step"] == wanted]
                p = (named or asked or at_clinic)[0]
                how = f"same clinic, booked by {a['name']}"
            if note: p["flags"].append(f"For Erin: {ev} on {a['date_time']}: {note}.")
            outcomes[id(p)].append((pile, f"{a['event_id']} at {a['date_time']}: {how}; heard: {source or 'not given'}"))
    for p in real:
        got = outcomes.get(id(p), [])
        demo = [e for k, e in got if k == "booked a demo"]; trial = [e for k, e in got if k == "started a trial"]
        if demo: p["pile"], p["pile_evidence"] = "booked a demo", demo[0]
        elif trial: p["pile"], p["pile_evidence"] = "started a trial", trial[0]
        elif p["sent_in_window"]: p["pile"], p["pile_evidence"] = "written to, nothing came of it", "; ".join(p["sent_in_window"])
        else: p["pile"], p["pile_evidence"] = "never written to", ""
    return review

def unmatched_mentions(people, activity, show_start):
    """A booking that mentions the show but matches nobody: maybe a conversation with no record."""
    out = []; real = [p for p in people if p["real"]]
    for a in activity:
        if a.get("event") not in ("demo booked", "trial started"): continue
        h = hear(a.get("detail", ""))
        if not re.search(r"owen|nadia|expo|booth|table|show|forum|conference", fold(h)): continue
        ts = parse_ts(a.get("date_time"))
        if not ts or (show_start and ts[0] < show_start): continue
        em = a.get("email") or ""
        if any(em in p["all_emails"] or same_clinic(a.get("clinic", ""), p["clinic"]) for p in real): continue
        out.append(dict(source=a.get("event_id", ""), text=f"{a.get('name','')}, {a.get('clinic','')}", reason=f"{a['event']} says \"{h}\" but matches no real conversation. Maybe someone with no record. Not counted in the piles."))
    return out

def write_issues(out, issues):
    with open(os.path.join(out, "input_issues.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "record", "reason", "review"]); w.writeheader(); w.writerows(issues)

# ---------- main ----------
def run(folder, out, state=None, before_followup=False, today=None):
    warnings, general, issues = [], [], []
    inp = find_inputs(folder)
    if not inp["scans"] and not inp["notes"]:
        raise SystemExit(f"Stopped: no scan export or booth notes found in {folder}. Put the show's files there and run again. Nothing was changed.")
    scans = load_scans(inp["scans"], warnings)
    cards, voices, lines = load_notes(inp["notes"], warnings, issues)
    activity = load_activity(inp["activity"], warnings, issues)
    for r in scans:
        if r["at"] and not parse_ts(r["at"]): issues.append(dict(file=os.path.basename(inp["scans"] or "scans"), record=r["id"], reason=f"Can't read the scan time '{r['at']}': not used for the show's dates", review="yes"))
        if not (r["name"] or r["email"] or r["clinic"]): issues.append(dict(file=os.path.basename(inp["scans"] or "scans"), record=r["id"], reason="Scan row with no name, address or clinic", review="yes"))
    people = cluster(scans + cards)
    place_voice(people, voices, general)
    place_list(people, lines, voices, general)
    for p in people: judge(p)
    for p in people:  # people at one clinic share its size and system
        for q in people:
            if p is not q and same_clinic(p["clinic"], q["clinic"]):
                p["system"] = p["system"] or q["system"]; p["locations"] = max(p["locations"], q["locations"])
    import memory as _mem
    mem = _mem.load(state, warnings)
    dne = [m for m in mem if m.get("status") == "do not email"]
    def block(p, kind, row, why):
        """The do-not-email list comes before everything: a new badge, a card, Owen's opinion, Nadia's promise, a trial, a new address."""
        if kind == "confirmed":
            p["dne"] = True; p["legal_hold"] = False; p["dne_suspected"] = False
            p["hold"] = f"HIGH RISK: on the do-not-email list since {row.get('date','')} ({row.get('show','earlier show')}). Matched on: {why}."
        else:
            if p.get("dne"): return
            p["dne_suspected"] = True
            p["hold"] = f"HIGH RISK, identity unsure: may be {row.get('name')}, who asked not to be emailed on {row.get('date','')}. Matched on: {why}. No draft until Erin says whether it's the same person."
        p["flags"].append(p["hold"])
    for p in people:
        hit = dne_check(p, dne)
        if hit and p["real"]: block(p, hit[0], hit[1], hit[2])
    def ts_of(rows):
        got = [parse_ts(x) for x in rows if x]; return [g for g in got if g]
    stamps = ts_of([r["at"] for r in scans]) or ts_of([v["at"] for v in voices])
    dates = sorted(g[0].strftime("%Y-%m-%d") for g in stamps)
    # The show runs from the first scan to the last scan. A date with no time covers that whole day.
    show_start = min((g[0] if g[1] else g[0].replace(hour=0, minute=0)) for g in stamps) if stamps else None
    show_end = max((g[0] if g[1] else g[0].replace(hour=23, minute=59)) for g in stamps) if stamps else None
    removal = piles(people, activity, show_end, show_start, issues)
    bounced = {a["email"] for a in activity if a.get("event") == "email bounced" and a.get("email")}
    for p in people:
        if p["real"] and p["email"] in bounced and not p["hold"]:
            other = [e for e in p["all_emails"] if e not in bounced]
            if other:
                p["flags"].append(f"For Owen: {p['email']} bounced. Draft now goes to {other[0]}; if that's the front desk, phone instead."); p["email"] = other[0]
            else:
                p["hold"] = f"Only address bounced ({p['email']}). Owen phones: {p['phone']}."; p["flags"].append(p["hold"])
    for u in unmatched_mentions(people, activity, show_start):
        general.append(u)
    for r in removal:
        row = dict(r, show="this show")
        for p in people:
            hit = dne_check(p, [row])
            if hit and p["real"]:
                if hit[0] == "confirmed":
                    p["dne"] = True; p["legal_hold"] = False; p["dne_suspected"] = False
                    p["hold"] = f"HIGH RISK: asked to be removed on {r['date']}. Matched on: {hit[2]}."; p["flags"].append(p["hold"])
                elif not p.get("dne"): block(p, "suspected", row, hit[2])
    for p in people:  # someone whose notes withdrew permission goes on the list for every show
        if p["real"] and p.get("revoked") and not p.get("dne"):
            p["dne"] = True; p["legal_hold"] = False
            if p["email"]: removal.append(dict(name=p["name"], email=p["email"], clinic=p["clinic"], date=(dates[-1] if dates else "")))
    import memory as _mem2
    show_key = _mem2.show_name(inp["notes"], dates)
    _mem2.apply_seen(people, mem, show_key, on_dne)
    import decisions as _dec
    decided = _dec.load(folder, out, warnings)
    _dec.apply(people, decided)
    if state: _mem2.save(state, mem, people, removal, show_key)
    for p in people:  # no address we can use: phone, or Erin finds one
        if p["real"] and not p["hold"] and not valid_email(p["email"]):
            p["no_email"] = True
            msg = f"No usable email address. Owen or Nadia phones: {p['phone']}." if p["phone"] else "No usable email address and no phone. Erin finds a way to reach them."
            p["flags"].append("For Erin: " + msg if not p["phone"] else msg)
    for p in people:
        if p["real"]:
            for b in p.get("bad_emails", []): issues.append(dict(file="show files", record=p["name"], reason=f"Unusable address '{b}'", review="yes"))
    os.makedirs(out, exist_ok=True)
    real = [p for p in people if p["real"]]
    order = {"hot": 0, "warm": 1, "cold": 2}
    import drafts as _dr0
    for p in real:
        tp = _dr0.topic(p)[0]
        p["safe_detail"] = _privacy.safe_detail(p, tp)
    real.sort(key=lambda p: (not p["first_batch"], -max(p["locations"], 1), order[p["priority"]], p["name"]))
    def sources(p):
        return "; ".join(sorted({r["id"] for r in p["records"]} | {n["source"] for n in p["notes"]}))
    with open(os.path.join(out, "people.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow("send_order name clinic city locations system priority next_step why from french email contact_source draft_status booth_detail sources day30_pile day30_evidence flags".split())
        for i, p in enumerate(real, 1):
            status = "no draft: " + p["hold"] if p["hold"] else ("no address, call" if p.get("no_email") else "call reminder" if p["next_step"] == "call back" else "draft")
            w.writerow([i, p["name"], p["clinic"], p["city"], p["locations"] or "", p["system"], p["priority"], p["next_step"], p["why"], p["sender"],
                        "yes" if p["french"] else "", p["email"], p["contact_source"], status, p.get("safe_detail", ""), sources(p), p.get("pile") or "", p.get("pile_evidence") or "", " | ".join(p["flags"])])
    with open(os.path.join(out, "flags.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["who_checks", "person", "clinic", "source", "reason"])
        def owner(fl):
            m = re.match(r"For ([A-Za-z ]+):", fl)
            return m.group(1) if m else ("Owen" if "Owen to" in fl else "Erin")
        for p in real:
            for fl in p["flags"]: w.writerow([owner(fl), p["name"], p["clinic"], sources(p), re.sub(r"^For [A-Za-z ]+: ", "", fl)])
        for g in general: w.writerow(["Owen", "(unplaced)", _privacy.clean_clauses(g["text"])[0], g["source"], g["reason"]])
    with open(os.path.join(out, "not_a_conversation.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["name", "clinic", "why", "sources"])
        for p in people:
            if not p["real"]: w.writerow([p["name"], p["clinic"], p["real_why"], sources(p)])
    with open(os.path.join(out, "run_notes.txt"), "w", encoding="utf-8") as f:
        f.write(f"Real conversations: {len(real)} of {len(people)} people; {len(scans)} scans, {len(cards)} cards, {len(voices)} voice notes, {len(lines)} list lines.\n")
        for x in warnings: f.write("WARNING: " + x + "\n")
    import drafts as _drafts
    rows = _drafts.write_all(dict(people=people, real=real, general=general, warnings=warnings, inputs=inp, scans=scans, cards=cards, voices=voices, lines=lines, activity=activity, decided=decided, memory_path=state), folder, out, inp["notes"], before_followup, today)
    raw_private = [c for p in people for c in p.get("private_raw", [])]
    write_issues(out, issues)
    return dict(people=people, real=real, general=general, warnings=warnings, removal=removal, drafts=rows, scans=scans, cards=cards, voices=voices, lines=lines, activity=activity, had_activity=bool(activity), issues=issues, raw_private=raw_private, show_start=show_start, show_end=show_end)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("show"); ap.add_argument("out"); ap.add_argument("--state", default=None)
    ap.add_argument("--by-show", action="store_true", help="keep each show's results in its own folder under the output folder")
    ap.add_argument("--before-followup", action="store_true", help="draft everyone as on day 1, ignoring emails already sent")
    a = ap.parse_args()
    out = a.out
    if a.by_show:
        import memory as _m
        f = find_inputs(a.show)
        if not f["scans"] and not f["notes"]:
            raise SystemExit(f"Stopped: no scan export or booth notes found in {a.show}. Put the show's files there and run again. Nothing was changed.")
        scans = load_scans(f["scans"], [])
        ds = [x["at"][:10] for x in scans if re.match(r"\d{4}-", x["at"] or "")]
        out = os.path.join(a.out, re.sub(r"[^A-Za-z0-9]+", "_", _m.show_name(f["notes"], ds)).strip("_"))
    r = run(a.show, out, a.state, a.before_followup)
    a.out = out
    print("Files used:", ", ".join(f"{k}: {os.path.basename(v) if v else 'NOT FOUND'}" for k, v in find_inputs(a.show).items()))
    print(f"{len(r['real'])} real conversations of {len(r['people'])} people. Output in {a.out}")
    for w in r["warnings"]: print("WARNING:", w)
