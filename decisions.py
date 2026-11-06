"""Decisions people typed into the Sheet. Read back on every run so a re-run never overwrites them."""
import csv, os, re, zipfile
import xml.etree.ElementTree as ET
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
FIELDS = ["person", "clinic", "decision", "by", "date"]

def key(name, clinic): return (name or "").strip().lower(), (clinic or "").strip().lower()

def read_xlsx(path):
    """Returns {sheet name: [row dicts]}. Reads the file Google Sheets downloads, standard library only."""
    z = zipfile.ZipFile(path); shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    out = {}
    for sh in wb.find("m:sheets", NS):
        rid = sh.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        tgt = rels[rid].lstrip("/"); tgt = tgt if tgt.startswith("xl/") else "xl/" + tgt
        rows = []
        for row in ET.fromstring(z.read(tgt)).iter("{%s}row" % NS["m"]):
            cells = {}
            for c in row.findall("m:c", NS):
                col = re.match(r"[A-Z]+", c.get("r")).group(0); t = c.get("t"); v = c.find("m:v", NS)
                if t == "s" and v is not None: val = shared[int(v.text)]
                elif t == "inlineStr": val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
                else: val = v.text if v is not None else ""
                cells[col] = val or ""
            rows.append(cells)
        out[sh.get("name")] = rows
    return out

def load(folder, out, warnings):
    """Decisions so far, plus any new ones in a Sheet file Erin put back in the show folder."""
    path = os.path.join(out, "decisions.csv"); got = {}
    if os.path.exists(path):
        for r in csv.DictReader(open(path, encoding="utf-8-sig")):
            got[key(r["person"], r["clinic"])] = r
    sheets = [os.path.join(r, f) for r, _, fs in os.walk(folder) for f in fs if f.lower().endswith(".xlsx") and not f.startswith("~")]
    for f in sheets:
        try: wb = read_xlsx(f)
        except Exception as e:
            warnings.append(f"Could not read decisions from {f}: {e}"); continue
        for tab in ("Erin", "Nadia", "Owen"):
            rows = wb.get(tab) or []
            head = next((i for i, r in enumerate(rows) if "Person" in r.values() and "Decision" in r.values()), None)
            if head is None: continue
            cols = {v: k for k, v in rows[head].items()}
            for r in rows[head + 1:]:
                d = (r.get(cols["Decision"]) or "").strip(); who = (r.get(cols["Person"]) or "").strip()
                if not d or not who: continue
                clinic = r.get(cols.get("Clinic", ""), "")
                got[key(who, clinic)] = dict(person=who, clinic=clinic, decision=d, by=tab, date=r.get(cols.get("Date", ""), ""))
    return got

def save(out, got):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "decisions.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(got.values())

def apply(people, got):
    """Owen / Nadia = that person sends. OK = checked, clear the wait. Hold = no draft.
    Nothing here can release someone on the do-not-email list or an N flag: only the law question can.
    The one exception is 'Different', from Erin, for someone who only might be on the list."""
    for p in people:
        d = got.get(key(p["name"], p["clinic"]))
        if not d or not p["real"]: continue
        val = d["decision"].strip().lower(); p["decision"] = d["decision"]
        if val in ("different", "different person"):
            if p.get("dne_suspected"):  # Erin checked: not the person who asked off
                p["flags"] = [f for f in p["flags"] if f != p["hold"]]
                p["hold"] = None; p["dne_suspected"] = False; p["decided"] = True
                p["flags"].append(f"Erin checked: not the person on the do-not-email list ({d.get('date','')}).")
            continue
        if val in ("same", "same person"):
            if p.get("dne_suspected"):
                p["dne"] = True; p["dne_suspected"] = False; p["decided"] = True
                p["flags"].append(f"Erin checked: same person as on the do-not-email list ({d.get('date','')}).")
            continue
        if val in ("owen", "nadia", "mine", "me"):
            p["sender"] = "Nadia" if val in ("nadia", "me", "mine") and d.get("by") == "Nadia" or val == "nadia" else ("Owen" if val == "owen" else p["sender"])
            p["decided"] = True
        elif val in ("ok", "okay", "done", "yes"): p["decided"] = True
        elif val in ("hold", "no", "don't send"):
            if not p["hold"]: p["hold"] = f"Held by {d.get('by','a person')}'s decision."
            p["decided"] = True
