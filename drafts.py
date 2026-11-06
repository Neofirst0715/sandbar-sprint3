"""Turns judged people into drafts, a Day 30 page and phone pages. Rules and the team's own words; no AI, nothing sends."""
import csv, html, json, os, re, urllib.parse
from datetime import datetime

import sandbar as _s
import privacy as _privacy
fold, first_ok, split_name, TITLES = _s.fold, _s.first_ok, _s.split_name, _s.TITLES
PRICE = 34
PLACE = {"demo_link": "[DEMO LINK]", "trial_link": "[TRIAL LINK]", "one_pager": "[ONE-PAGER]",
         "security_doc": "[SECURITY ONE-PAGER]", "hello_address": "[HELLO ADDRESS]"}
NUMW = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "twenty": 20}
ORD = {"first": "1st", "second": "2nd", "third": "3rd", "fourth": "4th", "fifth": "5th", "sixth": "6th", "seventh": "7th", "eighth": "8th",
       "ninth": "9th", "tenth": "10th", "twentieth": "20th", "twenty eighth": "28th", "twenty eight": "28th"}

def load_settings(folder):
    s = dict(PLACE)
    p = os.path.join(folder, "settings.json")
    if os.path.exists(p):
        s.update({k: v for k, v in json.load(open(p, encoding="utf-8")).items() if v})
    return s

def show_info(folder, notes_path):
    city, name = "", ""
    if notes_path:
        about = json.load(open(notes_path, encoding="utf-8")).get("about", "")
        m = re.search(r"\(([^,()]+),", about); city = m.group(1).strip() if m else ""
        m = re.search(r"from the (.+?) booth", about); name = m.group(1).strip() if m else ""
    return city, name

def greeting(p):
    """The name Owen actually uses: Steve, not Stephen; Jen, not Jennifer."""
    raw = p["name"].split(",")[0].split()
    raw = [t for t in raw if fold(t).strip(".") not in TITLES]
    first = " ".join(raw[:-1]) if len(raw) > 1 else (raw[0] if raw else "")
    for r in p["records"]:  # replace an initial with a full name
        if len(first.strip(".")) == 1:
            o = r["name"].split(",")[0].split(); o = [t for t in o if fold(t).strip(".") not in TITLES]
            if len(o) > 1 and len(o[0].strip(".")) > 1: first = o[0]
    text = " ".join(n["text"] for n in p["notes"]) + " " + " ".join(r["text"] + " " + r["name"] for r in p["records"])
    best = first
    groups = [g for g in _s.NICK if fold(first) in g]
    for t in re.findall(r"[A-Za-zÀ-ÿ']+", text):
        ft = fold(t)
        if len(ft) >= 3 and len(ft) < len(fold(best)) and any(ft in g for g in groups) and ft not in {"will", "bill"}:
            best = t
    return best[:1].upper() + best[1:]

# (pattern, English sentence, kind, French sentence or None). {s} = the booking system they are on.
TOPICS = [
    (r"double.?book\w* (?:her|his|their) ([a-z]+ \w+)", "You mentioned {s} double-booked your {1}", "pain", None),
    (r"renew\w*.*(?:compare|end of the year)|compare before", "You wanted to compare before your {s} renewal at the end of the year", "pain", "Votre renouvellement {s} arrive en fin d'année"),
    (r"reports? (?:r |are |is )?(?:useless|garbage|no use)", "You mentioned the reports on {s} are no use to you", "pain", None),
    (r"(?:hates|hate) the reporting|can'?t get a number", "You mentioned you can't get a number out of {s}'s reporting", "pain", None),
    (r"\$ per practitioner|pricing per practitioner", "You wanted the price per practitioner", "ask", None),
    (r"overwrit", "You mentioned your RMTs keep overwriting each other on the shared calendar", "pain", None),
    (r"logging \w+ \w+ out", "You mentioned {s} keeps logging your RMTs out", "pain", "Owen m'a dit que {s} déconnecte vos massothérapeutes"),
    (r"charging \w+ per text|txt reminders cost extra|text reminder", "You mentioned {s} charges extra for text reminders", "pain", "Owen m'a dit que {s} vous facture maintenant chaque rappel texte"),
    (r"drowning in phone", "You mentioned your front desk is drowning in phone bookings", "pain", None),
    (r"sick of", "You mentioned you're sick of answering the phone all day", "pain", None),
    (r"mandarin", "You asked whether reminders can go out in Mandarin, and I'm checking that for you", "ask", None),
    (r"front desk shared|shared front desk", "You mentioned one front desk is shared between your clinics", "pain", None),
    (r"(?:try|trial).*(?:two|2) rmts|(?:two|2) rmts first", "You wanted to try it with your two RMTs first", "ask", None),
    (r"in writing", "You wanted the pricing in writing for your business partner", "ask", None),
    (r"ditched|refugee|left book", "You mentioned you left {left} and you're running the clinic off a spreadsheet", "pain", None),
    (r"own google calendar|master spreadsheet", "You mentioned each clinic runs its own Google Calendar and it all gets copied into one spreadsheet", "pain", None),
    (r"every front desk", "You mentioned every front desk is still on a paper book", "pain", None),
    (r"second location|2nd loc|new place", "You mentioned the new location", "pain", None),
    (r"no.?shows", "You mentioned the no-shows you're losing every week", "pain", None),
    (r"import from|import ", "You asked if we can import your data from {s}", "ask", None),
    (r"evening slots", "You mentioned clients keep asking for evening slots", "pain", None),
    (r"deposit", "You mentioned you'd like a deposit taken when clients book", "pain", None),
    (r"intake form", "You mentioned you'd like intake forms filled in before the first visit", "pain", None),
    (r"cancellation", "You mentioned you'd like clients to grab cancellation slots online", "pain", None),
    (r"rebook", "You mentioned your front desk spends Monday mornings rebooking the weekend", "pain", None),
    (r"direct billing", "You asked about direct billing", "ask", None),
    (r"rota|schedule and bookings|bookings separate", "You mentioned your staff schedule and bookings live in two different places", "pain", None),
    (r"phone rings|phones ring", "You mentioned the phones ring through the whole lunch hour", "pain", None),
    (r"price went up", "You mentioned {s}'s price went up", "pain", None),
    (r"new grad|opening clinic", "You mentioned you're looking at opening your own clinic later", "later", None),
    (r"\bexcel\b", "You mentioned you're running things in Excel", "tool", None),
    (r"(?<!pricing )(?<!security )\bsheets?\b|spreadsheet", "You mentioned you're running things on a spreadsheet", "tool", None),
    (r"\bpaper\b", "You mentioned you're still on a paper book", "tool", None),
    (r"gcal|google cal", "You mentioned you're running things on Google Calendar", "tool", None),
    (r"show the owner|take to the owner|for (the |his |her )?owner", "You wanted something to show your owner", "ask", None),
]

def topic(p):
    t = fold(p["booth_detail"])
    sysname = p.get("system") or "your current system"
    left = "your old system"
    m = re.search(r"(bookstead|book stead|clinivo|clean evo|pracshift|prac shift)", t)
    if m: left = {"b": "Bookstead", "c": "Clinivo", "p": "Pracshift"}[m.group(1)[0]]
    for pat, en, kind, fr in TOPICS:
        m = re.search(pat, t)
        if m and not ("{s}" in en and not p.get("system") and "import" not in pat):
            txt = en.replace("{s}", sysname).replace("{left}", left)
            if "{1}" in txt: txt = txt.replace("{1}", m.group(1).replace("saturday", "Saturday").replace("rmts", "RMTs"))
            return txt, kind, (fr.replace("{s}", sysname) if fr else None)
    if p.get("system"):
        return f"You mentioned you're on {p['system']}", "tool", None
    return "", "", None

def practitioners(p):
    m = re.search(r"\b(\d+|" + "|".join(NUMW) + r")\s+(physios?|practitioners?|clinicians?|rmts?)\b", fold(p["booth_detail"]))
    if not m: return 0
    return int(m.group(1)) if m.group(1).isdigit() else NUMW[m.group(1)]

def demo_extra(p):
    t = fold(p["booth_detail"]); bits = []
    m = re.search(r"owner\s*=\s*(dr\.?\s*\w+)", t)
    if m: bits.append(f"Pick a time {m.group(1).replace('dr', 'Dr', 1).title()} can make.")
    elif "owner has to be" in t: bits.append("Pick a time your owner can make.")
    if re.search(r"manager", t) and not bits: bits.append("Bring your managers along.")
    if "ops lead" in t: bits.append("Bring your ops lead.")
    m = re.search(r"back on the ([a-z]+(?: [a-z]+)?|\d+\w*)", t)
    if m: bits.append(f"Any time after you're back on the {ORD.get(m.group(1), m.group(1))} works.")
    return " ".join(bits)

def step_fallback(p):
    return {"demo": "You asked to see a demo", "pricing": "You asked about pricing", "trial": "You wanted to try it"}.get(p["next_step"], "")

def build_draft(p, show, st, late):
    """Returns dict(subject, body, kind, notes). Does not decide who may be emailed: that is judge()'s job."""
    f, clinic = greeting(p), re.split(r"\s+(?:Physio|Massage|Health|Rehab|Therapeutic|Sports|Acupuncture|Wellness)", p["clinic"])[0]
    where = f"in {show[0]}" if show[0] else "at the show"
    hello = f"{f}, good to meet you {where}."
    if late and p["first_batch"]: hello = f"{f}, good to meet you {where}, and sorry this took me a while."
    sign = p["sender"]; notes = []
    nadia = "me" if sign == "Nadia" else "Nadia"
    if re.search(r"\b(wk|week) of\b|monday the", fold(p["booth_detail"])): notes.append("They named a time at the booth. Check it fits Nadia's calendar before promising it.")
    tp, kind, fr = topic(p)
    alltext = fold(p["booth_detail"] + " " + " ".join(r["text"] for r in p["records"]))
    if not tp and not step_fallback(p): notes.append("Nothing specific written down: add the one thing you remember.")
    if not tp and step_fallback(p): tp, kind = step_fallback(p), "ask"; notes.append("Only what they asked for is on record: add one thing you talked about if you remember it.")
    line = (tp + ". ") if tp else ""
    step = p["next_step"]; link_used = []
    # French conversations: Nadia writes in French; never a demo link in a call-back
    if p["french"]:
        return french_draft(p, f, show, st, late, fr, notes)
    if step == "demo":
        subject = f"{clinic} demo"; extra = demo_extra(p)
        body = f"{hello} {line}Here's where to book the demo with {nadia}: {st['demo_link']}. {extra}".strip() + f" {sign}."
    elif step == "pricing":
        n = practitioners(p); sum_ = f" For your {n} practitioners that's ${n * PRICE} a month." if n else ""
        subject = f"Pricing for {p['clinic']}"
        tail = ""
        if p.get("aside"): tail = f" If you want to try it, here's where you start a trial: {st['trial_link']}."
        if p.get("only_what_asked"): tail = " That's all you asked for, and I won't add you to any list."
        body = f"{hello} {line}It's ${PRICE} per practitioner per month.{sum_}{tail} {sign}."
    elif step == "trial":
        subject = f"Trial for {clinic}"
        body = f"{hello} {line}Here's where to start the trial: {st['trial_link']}. I'm around if you get stuck. {sign}."
    elif step == "call back":
        mon = re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b", alltext)
        short = re.search(r"\b(mid[- ]?|around |early |late )(jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b( \d+\w*)?", alltext)
        when = "after Thanksgiving" if "thanksgiving" in alltext else re.sub(r"\b(jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b", lambda m: m.group(1).title(), short.group(0).strip()) if short else f"in {mon.group(1).title()}" if mon else "once the new location is open" if re.search(r"new place|new location|second location|2nd loc", alltext) else "when you said"
        subject = "Looking forward to it"
        body = f"{hello} I'll call you {when}, not before. Looking forward to it. {sign}."
        notes.insert(0, f"Reminder for {sign}: call {p['name']} {p.get('phone','')} {when}. The call is the job; this note is optional.")
    elif step == "send info" and re.search(r"security|soc ?2", alltext + " " + fold(" ".join(n["text"] for n in p["notes"]))):
        subject = f"{clinic} - the security one-pager for your IT team"
        body = f"{hello} {line}Here's the security one-pager for your IT team: {st['security_doc']}. I'll give you a call once they've had a look. {sign}."
    elif step == "send info":
        for_owner = re.search(r"for (the |his |her |their )?owner|show the owner|to the owner|take to", alltext)
        if for_owner:
            subject = f"{clinic} - something for your owner"
            body = (f"{hello} {line}Here's the one-pager to pass along: {st['one_pager']}. It's ${PRICE} per practitioner per month. "
                    f"Who's the best person to talk to about it, and when's a good time for me to call? {sign}.")
        else:
            subject = f"Good to meet you {where}"
            attach = f"Here's the one-pager you asked for: {st['one_pager']}. " if re.search(r"brochure|one.?pager", alltext) else ""
            nextyr = re.search(r"maybe next y|not ready|just browsing", alltext)
            book = f"If you want to see how we'd handle that, here's where to book a time with {nadia}: {st['demo_link']}. " if p["priority"] == "warm" and not nextyr and not p.get("only_what_asked") else ""
            if kind == "tool" and not attach and not book:
                body = f"{hello} {line[:-2]}, so if that ever starts getting messy, give me a shout. {sign}."
            else:
                body = f"{hello} {line}{attach}{book}".strip() + f" {sign}."
    else:  # thank-you note
        subject = f"Good to meet you {where}"
        nextyr = re.search(r"maybe next y", alltext)
        if not tp and nextyr: body = f"{hello} No rush at all, so give me a shout whenever the timing's better. {sign}."
        elif not tp: body = f"{hello} Thanks for stopping by, and give me a shout if I can help. {sign}."
        elif kind == "later": body = f"{hello} {tp}, so give me a shout when you get there. {sign}."
        elif nextyr: body = f"{hello} {tp}. No rush at all, so give me a shout whenever the timing's better. {sign}."
        elif kind == "tool": body = f"{hello} {tp}, so if that ever starts getting messy, give me a shout. {sign}."
        else: body = f"{hello} {tp}, so if you ever want to see how we'd handle that, give me a shout. {sign}."
    return dict(subject=subject, body=re.sub(r"\s+", " ", body).strip(), notes=notes)

def french_draft(p, f, show, st, late, fr, notes):
    where = f"à {show[0]}" if show[0] else "au salon"
    late_note = late and p["first_batch"]
    head = f"{f}, désolée pour le délai. " if late_note else f"{f}, "
    step = p["next_step"]; line = (fr + ". ") if fr else ""
    if not fr and step not in ("call back",): notes.append("French draft has no booth detail yet: Nadia adds the one thing they talked about.")
    if step == "call back":
        subject = "Notre appel"
        body = f"{head}{'Je' if late_note else 'je'} vous avais promis un appel{" après l'Action de grâce" if "action de grace" in fold(" ".join(r["text"] for r in p["records"])) else ""}. {line}Je vous appelle cette semaine, quel moment vous convient le mieux? Nadia."
        notes.insert(0, f"Reminder for Nadia: call {p['name'].split(',')[0]} {p.get('phone','')} in French. A call date, not a demo link.")
    elif step == "demo":
        subject = "Une démo"; body = f"{head}{line}Voici le lien pour réserver une démo avec moi : {st['demo_link']}. Nadia."
    elif step == "pricing":
        subject = "Nos prix"; body = f"{head}{line}C'est {PRICE} $ par praticien par mois. Nadia."
    elif step == "trial":
        subject = "Votre essai"; body = f"{head}{line}Voici le lien pour commencer l'essai : {st['trial_link']}. Je suis là si vous êtes bloquée. Nadia."
    else:
        subject = f"Suite au salon {where}"
        body = f"{head}{line}Si vous voulez en parler un jour, écrivez-moi. Nadia."
    return dict(subject=subject, body=re.sub(r"\s+", " ", body).strip(), notes=notes)

BLOCKING = re.compile(r"Was this you|Decide who sends|Sources disagree|placed by a guess|Only a question mark|already (booked|started)|Check it exists|because of the N flag")
def write_all(res, show_folder, out, notes_path, before_followup=False, today=None):
    st = load_settings(show_folder); show = show_info(show_folder, notes_path)
    dates = [r["at"][:10] for p in res["people"] for r in p["records"] if r["kind"] == "scan" and re.match(r"\d{4}-", r["at"] or "")]
    today = today or datetime.now()
    age = (today - datetime.strptime(max(dates), "%Y-%m-%d")).days if dates else 0
    late = age > 21
    rows = []
    for i, p in enumerate(res["real"], 1):
        d = dict(send_order=i, name=p["name"], clinic=p["clinic"], priority=p["priority"], next_step=p["next_step"], sender=p["sender"], language="French" if p["french"] else "English",
                 to=p["email"], cc=st["hello_address"], subject="", body="", status="", check="", p=p, waiting_on="")
        if p["hold"]:
            d["status"] = ("HOLD — LEGAL REVIEW REQUIRED: " if p.get("legal_hold") else "NO DRAFT: ") + p["hold"]; rows.append(d); continue
        if p.get("no_email"):
            if p["phone"]:
                p["call_instead"] = f"Can't be reached by email. Call {p['name']} at {p['phone']}" + (f" about the {p['next_step']} they asked for." if p["first_batch"] else ".")
                d["status"] = "CALL: no usable email address, so no draft"
            else:
                d["status"] = "NO DRAFT: no usable email address and no phone. Erin finds a way to reach them."
            rows.append(d); continue
        alltxt = fold(" ".join(r["text"] for r in p["records"]) + " " + " ".join(n["text"] for n in p["notes"]))
        if p["next_step"] == "send info" and re.search(r"security|soc ?2", alltxt) and st["security_doc"] == PLACE["security_doc"] and not p.get("sent"):
            p["call_instead"] = "They asked for a security document and we don't have one to send yet. Owen calls instead."
            d["status"] = "CALL: security document not set, so no draft that pretends (Nadia, Nov 4)"; rows.append(d); continue
        if late and p["next_step"] == "thank-you note" and not p.get("sent") and not before_followup:
            d["status"] = "NO DRAFT: a generic note more than three weeks after the show is pointless (Erin, Nadia, Nov 2)"; rows.append(d); continue
        if p["next_step"] == "call back" and re.search(r"\b(no emails?|do not email|don'?t email|(phone|call) only)\b", alltxt):
            p["call_instead"] = f"Asked for a call and no email. Call {p['name']} {p.get('phone', '')}."
            d["status"] = "CALL: asked for a call and no email, so no draft"; rows.append(d); continue
        b = build_draft(p, show, st, late)
        d["subject"], d["body"] = b["subject"], b["body"]
        stop = _privacy.scan_draft(b["subject"] + " " + b["body"], p)
        if stop:
            p["flags"].append(f"For Erin: privacy review required: the draft {stop}. It was not offered.")
            d["subject"], d["body"] = "", ""
            d["status"] = "PRIVACY REVIEW REQUIRED: no draft offered until Erin checks"; rows.append(d); continue
        notes = b["notes"] + [re.sub(r"^For [A-Za-z ]+: ", "", x) for x in p["flags"]]
        if age > 30 and p["next_step"] == "thank-you note" and not p.get("sent"):
            notes.append("Over a month since the show: a generic note may be pointless. Your call.")
        d["check"] = " | ".join(notes)
        blocking = [x for x in p["flags"] if BLOCKING.search(x)]
        sent = p.get("sent") or []
        if not before_followup and sent:
            d["status"] = f"ALREADY WRITTEN TO ({sent[0][:10]}): do not send again"
        elif not before_followup and p.get("pile") == "booked a demo" and p["next_step"] == "demo":
            d["status"] = "ALREADY BOOKED: no booking link"
            d["body"] = f"{greeting(p)}, I see you've booked a demo with Nadia. See you then. {p['sender']}."
        elif blocking and not p.get("decided"):
            m = re.match(r"For ([A-Za-z ]+):", blocking[0])
            d["waiting_on"] = m.group(1) if m else "Owen"
            d["status"] = f"WAITING on {d['waiting_on']}: decide first"
        elif p["next_step"] == "call back": d["status"] = "CALL: reminder first"
        else: d["status"] = "READY: read, fix a word, send"
        rows.append(d)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "drafts.csv"), "w", newline="", encoding="utf-8") as f:
        fields = "send_order name clinic priority next_step sender language to cc subject body status check".split()
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    write_piles(res, out, show)
    import sheet as _sheet, decisions as _dec
    _sheet.write(os.path.join(out, "Sandbar_follow_up.xlsx"), res, rows, show, before_followup)
    _dec.save(out, res.get("decided") or {})
    return rows

PILES = ["booked a demo", "started a trial", "written to, nothing came of it", "never written to"]
def write_piles(res, out, show):
    real = res["real"]
    with open(os.path.join(out, "piles.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["pile", "name", "clinic", "why_it_is_in_this_pile"])
        for pile in PILES:
            for p in sorted((x for x in real if x.get("pile") == pile), key=lambda x: x["name"]):
                w.writerow([pile, p["name"], p["clinic"], p.get("pile_evidence", "")])
    show_name = " ".join(x for x in [show[1], show[0]] if x) or "This show"
    parts = [f"<h1>{html.escape(show_name)}: 30 days later</h1><p>{len(real)} real conversations. Demos booked count even if the demo hasn't happened. This page can't say who became a paying clinic.</p>",
             '<div class="tiles">' + "".join(f'<div><b>{sum(1 for p in real if p.get("pile") == pile)}</b>{pile}</div>' for pile in PILES) + "</div>"]
    for pile in PILES:
        items = sorted((x for x in real if x.get("pile") == pile), key=lambda x: x["name"])
        lis = "".join(f"<li>{html.escape(p['name'])}, {html.escape(p['clinic'])}" + (f'<small>{html.escape(p["pile_evidence"])}</small>' if pile in PILES[:2] else "") + "</li>" for p in items)
        parts.append(f"<h2>{pile} ({len(items)})</h2><ul>{lis}</ul>")
    page(os.path.join(out, "day30_page.html"), show_name + ": 30 days later", "".join(parts))

CSS = """body{font:16px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;margin:0 auto;max-width:720px;padding:16px;color:#1c1c1a;background:#fff}
h1{font-size:22px;margin:.2em 0}h2{font-size:17px;margin:1.4em 0 .4em}small{display:block;color:#666;font-size:13px}ul{padding-left:18px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px}.tiles div{border:1px solid #ddd;border-radius:8px;padding:10px}.tiles b{display:block;font-size:26px}
.d{border:1px solid #ddd;border-radius:10px;padding:12px;margin:12px 0}.d h3{margin:0;font-size:16px}.d p{margin:.5em 0;white-space:pre-wrap}
.c{background:#fff6dd;border-radius:6px;padding:6px 8px;font-size:14px}.a{display:block;text-align:center;background:#1c1c1a;color:#fff;padding:12px;border-radius:8px;text-decoration:none;font-weight:600}.w{color:#a33;font-size:14px}"""
def page(path, title, body):
    open(path, "w", encoding="utf-8").write(f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}</style></head><body>{body}</body></html>')
