"""Turns whatever Erin dropped on the upload page into one tidy input folder for the engine.
CSV, Excel and JSON all work; each table is recognised by its header row, not its file name.
A sheet it doesn't recognise is ignored and named on the Erin page. Standard library only."""
import csv, glob, json, os, re, shutil
from datetime import datetime, timedelta
import decisions as _dec

def _cols(rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    return keys

def _read_csv(path, issues=None):
    """Rows as dicts. Duplicate headers keep the first column; blank headers are dropped; bad rows are reported, not lost silently."""
    issues = issues if issues is not None else []
    name = os.path.basename(path)
    for enc in ("utf-8-sig", "cp1252"):
        try:
            with open(path, encoding=enc, newline="") as f: table = list(csv.reader(f))
            break
        except UnicodeDecodeError: continue
    else:
        issues.append(dict(file=name, record="whole file", reason="Could not read the text encoding", review="yes")); return []
    table = [r for r in table if any((c or "").strip() for c in r)]
    if not table:
        issues.append(dict(file=name, record="whole file", reason="Empty file", review="yes")); return []
    head, seen = [], set()
    for c in table[0]:
        c = (c or "").strip()
        if c and c.lower() in seen:
            issues.append(dict(file=name, record="header", reason=f"Column '{c}' appears twice: the first one is used", review="yes")); c = ""
        elif c: seen.add(c.lower())
        head.append(c)
    rows = []
    for i, r in enumerate(table[1:], 2):
        if len(r) != len(table[0]):
            issues.append(dict(file=name, record=f"row {i}", reason=f"Row has {len(r)} columns, header has {len(table[0])}. Read as far as it goes. Check it.", review="yes"))
        rows.append({h: (r[j].strip() if j < len(r) else "") for j, h in enumerate(head) if h})
    return rows

def _excel_date(col, val):
    """Excel stores dates as numbers. Dates must stay real dates or the three-week and day-30 rules can't work."""
    if re.search(r"date|time|scanned|recorded|typed|when", col.lower()) and re.fullmatch(r"\d{5}(\.\d+)?", (val or "").strip()):
        return (datetime(1899, 12, 30) + timedelta(days=float(val))).strftime("%Y-%m-%dT%H:%M:%S")
    return val

def _sheet_rows(rows):
    if not rows: return []
    letters = sorted({k for r in rows for k in r}, key=lambda x: (len(x), x))
    head = [(rows[0].get(l) or "").strip() or l for l in letters]
    out = []
    for r in rows[1:]:
        d = {h: _excel_date(h, r.get(l, "")) for h, l in zip(head, letters)}
        if any((v or "").strip() for v in d.values()): out.append(d)
    return out

def kind_of(rows):
    """scans, cards, voice, list, activity, sent or None, from the header alone."""
    if not rows: return None
    h = [str(x).lower().replace("_", " ") for x in rows[0].keys()]
    has = lambda *ks: any(any(k in c for k in ks) for c in h)
    if has("day30", "promised next step"): return None  # an answer key or recount, never input
    if has("transcript"): return "voice"
    if has("back of card", "card id"): return "cards"
    if has("line id") and has("text") and not has("email"): return "list"
    if has("event") and has("email"): return "activity"
    if has("email", "e-mail", "courriel") and has("company", "clinic", "organisation", "organization", "practice", "business", "employer", "facility") and has("first", "given", "name", "surname"): return "scans"
    if has("email") and len(h) <= 3 and not has("name", "clinic", "company"): return "sent"
    if has("text", "note") and len(h) <= 3: return "list"
    return None

def _pick(r, *keys):
    for k in keys:
        for c in r:
            if k in str(c).lower().replace("_", " "):
                if (r[c] or "").strip(): return r[c].strip()
    return ""

def _city(show):
    words = [w for w in re.sub(r"\b(19|20)\d\d\b", " ", show or "").split()]
    if len(words) > 1 and re.search(r"expo|forum|conference|show|summit", show or "", re.I): return words[-1]
    return " ".join(words)

def prepare(data_dir, input_dir, show, settings=None):
    """Writes badge-scans.csv, booth-notes.json, after-show-activity.csv and settings.json. Returns what it used."""
    if os.path.isdir(input_dir): shutil.rmtree(input_dir)
    os.makedirs(input_dir)
    used, ignored, issues = [], [], []
    tables, booth = {}, {"cards": [], "voice_notes": [], "owen_list": {"lines": []}}
    about = ""
    for path in sorted(glob.glob(os.path.join(data_dir, "**", "*"), recursive=True)):
        if not os.path.isfile(path) or os.path.basename(path).startswith((".", "~")): continue
        name = os.path.basename(path); low = name.lower()
        try:
            if low.endswith(".json"):
                if low.startswith("settings"): continue
                d = json.load(open(path, encoding="utf-8-sig"))
                about = about or d.get("about", "") or ""
                def good(rows, label):
                    out = []
                    for i, x in enumerate(rows or [], 1):
                        if isinstance(x, dict): out.append(x)
                        else: issues.append(dict(file=name, record=f"{label} item {i}", reason="Empty or broken record, skipped", review="yes"))
                    return out
                booth["cards"] += good(d.get("cards"), "card")
                booth["voice_notes"] += good(d.get("voice_notes"), "voice note")
                booth["owen_list"]["lines"] += good((d.get("owen_list") or {}).get("lines"), "list line")
                used.append(name)
            elif low.endswith(".csv"):
                rows = _read_csv(path, issues); k = None if "recount" in low else kind_of(rows)
                if k: tables.setdefault(k, []).append((name, rows)); used.append(name)
                else:
                    ignored.append(f"{name}: not one of the show files")
                    if rows: issues.append(dict(file=name, record="whole file", reason="Columns not recognised, so this file was not read. Look at it: if it's the scan export, tell whoever looks after the tool.", review="yes"))
            elif low.endswith(".xlsx"):
                sheets = _dec.read_xlsx(path)
                if "Erin" in sheets and "Owen" in sheets:  # our own Sheet, sent back with decisions typed in it
                    shutil.copyfile(path, os.path.join(input_dir, name)); used.append(f"{name} (decisions)"); continue
                for sn, raw in sheets.items():
                    rows = _sheet_rows(raw); k = kind_of(rows)
                    if k: tables.setdefault(k, []).append((f"{name} / {sn}", rows)); used.append(f"{name} / {sn}")
                    elif rows: ignored.append(f"{name} / {sn}: columns not recognised")
            else: ignored.append(f"{name}: not CSV, Excel or JSON")
        except Exception as ex:
            ignored.append(f"{name}: could not read it ({str(ex)[:80]})")
            issues.append(dict(file=name, record="whole file", reason=f"Could not read it: {str(ex)[:100]}", review="yes"))
    if "scans" in tables:
        rows = [r for _, rs in tables["scans"] for r in rs]; cols = _cols(rows)
        with open(os.path.join(input_dir, "badge-scans.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    for _, rows in tables.get("cards", []):
        for i, r in enumerate(rows):
            nm = _pick(r, "name") or (_pick(r, "first") + " " + _pick(r, "last")).strip()
            booth["cards"].append(dict(card_id=_pick(r, "card id") or f"C{len(booth['cards'])+1:02d}", name=nm, title=_pick(r, "title", "role"), clinic=_pick(r, "clinic", "company"),
                                       email=_pick(r, "email", "e-mail").lower(), phone=_pick(r, "phone"), back_of_card=_pick(r, "back of card", "note", "text"),
                                       collected_by=_pick(r, "collected by", "by"), typed_on=_pick(r, "typed on", "date")))
    for _, rows in tables.get("voice", []):
        for r in rows:
            v = dict(note_id=_pick(r, "note id") or f"V{len(booth['voice_notes'])+1:02d}", transcript=_pick(r, "transcript"), recorded_at=_pick(r, "recorded at", "date", "time"))
            by = _pick(r, "recorded by", "speaker")
            if by: v["recorded_by"] = by
            booth["voice_notes"].append(v)
    for _, rows in tables.get("list", []):
        for r in rows:
            booth["owen_list"]["lines"].append(dict(line_id=_pick(r, "line id") or f"L{len(booth['owen_list']['lines'])+1:02d}", text=_pick(r, "text", "line", "note")))
    if any(booth["cards"]) or booth["voice_notes"] or booth["owen_list"]["lines"] or about:
        booth["about"] = about or f"Typed up from the {show} booth ({_city(show)}, )"
        with open(os.path.join(input_dir, "booth-notes.json"), "w", encoding="utf-8") as f: json.dump(booth, f, ensure_ascii=False, indent=1)
    events = []
    # event_id also contains "event": read the event column exactly
    if tables.get("activity"):
        for _, rows in tables["activity"]:
            for r in rows:
                evc = next((c for c in r if str(c).lower().replace("_", " ").strip() in ("event", "event type", "type")), None) or next((c for c in r if "event" in str(c).lower() and "id" not in str(c).lower()), None)
                events.append(dict(event_id=_pick(r, "event id") or f"E{len(events)+1:03d}", date_time=_pick(r, "date", "time"), event=(r.get(evc) or "").strip().lower() if evc else "",
                                   channel=_pick(r, "channel", "source"), name=_pick(r, "name"), email=_pick(r, "email").lower(), clinic=_pick(r, "clinic", "company"), detail=_pick(r, "detail", "note", "subject")))
    for name, rows in tables.get("sent", []):
        for r in rows:
            em = _pick(r, "email").lower()
            if em: events.append(dict(event_id=f"SENT{len(events)+1:03d}", date_time=_pick(r, "date", "sent") or "", event="email sent", channel="already-sent list", name="", email=em, clinic="", detail=""))
    if events:
        with open(os.path.join(input_dir, "after-show-activity.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["event_id", "date_time", "event", "channel", "name", "email", "clinic", "detail"]); w.writeheader(); w.writerows(events)
    if settings:
        with open(os.path.join(input_dir, "settings.json"), "w", encoding="utf-8") as f: json.dump(settings, f, indent=1)
    if "scans" not in tables: issues.append(dict(file="show files", record="scan export", reason="No scan export found in what was dropped", review="yes"))
    return dict(used=used, ignored=ignored, issues=issues)
