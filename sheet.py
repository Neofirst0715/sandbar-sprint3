"""Writes one .xlsx with no extra libraries. Upload to a restricted Google Drive folder and open with Google Sheets."""
import privacy as _privacy
import re, zipfile
from xml.sax.saxutils import escape
PILES = ["booked a demo", "started a trial", "written to, nothing came of it", "never written to"]

def col(i):
    s = ""
    i += 1
    while i: i, r = divmod(i - 1, 26); s = chr(65 + r) + s
    return s

def sheet_xml(rows, widths, freeze=None):
    out = ['<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">']
    if freeze is not None:
        out.append(f'<sheetViews><sheetView workbookViewId="0"><pane ySplit="{freeze}" topLeftCell="A{freeze+1}" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>')
    out.append("<cols>" + "".join(f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths)) + "</cols><sheetData>")
    for r, row in enumerate(rows, 1):
        style, vals = row if isinstance(row, tuple) else (1, row)
        cells = "".join(f'<c r="{col(c)}{r}" t="inlineStr" s="{style}"><is><t xml:space="preserve">{escape(str(v))}</t></is></c>' for c, v in enumerate(vals) if v not in ("", None))
        out.append(f'<row r="{r}">{cells}</row>')
    out.append("</sheetData></worksheet>")
    return "".join(out)

STYLES = '''<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="3"><font><sz val="11"/><name val="Arial"/></font><font><b/><sz val="11"/><name val="Arial"/></font><font><b/><sz val="15"/><name val="Arial"/></font></fonts>
<fills count="4"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFE8EEF4"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFFFF3D6"/></patternFill></fill></fills>
<borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs>
<cellXfs count="5"><xf/><xf applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf><xf fontId="1" fillId="2" applyFont="1" applyFill="1" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf><xf fontId="2" applyFont="1"/><xf fillId="3" applyFill="1" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf></cellXfs></styleSheet>'''

H, T, N = 2, 3, 1
def write(path, res, rows, show, before_followup):
    real = res["real"]; show_name = " ".join(x for x in [show[1], show[0]] if x) or "This show"
    wanted = rows
    def tab_for(who):
        data = [(T, [f"{who}: drafts, promises first"]), (N, ["Nothing sends on its own. Read, fix a word, copy into your mail, cc hello. Type a decision only where a row is waiting: OK, Hold" + (", Owen or Nadia." if who != "Erin" else ".")]),
                (H, ["#", "Status", "Person", "Clinic", "To", "Subject", "Draft", "Check first", "Decision"])]
        for r in wanted:
            if r["sender"] != who or not r["body"] or r["status"].startswith("ALREADY WRITTEN"): continue
            style = 4 if r["status"].startswith(("WAITING", "CALL", "ALREADY BOOKED")) else N
            data.append((style, [r["send_order"], r["status"], r["name"], r["clinic"], r["to"], r["subject"], r["body"], r["check"], (r["p"].get("decision") or "")]))
        return data
    owen, nadia = tab_for("Owen"), tab_for("Nadia")
    # Erin's worklist
    erin = [(T, ["Erin: what needs a person"]), (N, ["Type a decision in the last column: OK or Hold. Download this Sheet into the show folder and run again: decisions stay. N-flag and do-not-email people stay held whatever is typed."]),
            (H, ["Who decides", "Person", "Clinic", "Why it's here", "Came from", "Contact came from", "Decision"])]
    def owner(fl):
        m = re.match(r"For ([A-Za-z ]+):", fl)
        return m.group(1) if m else ("Owen" if "Owen to" in fl else "Erin")
    for p in real:
        srcs = "; ".join(sorted({x["id"] for x in p["records"]} | {n["source"] for n in p["notes"]}))
        for fl in p["flags"]:
            erin.append((N, [owner(fl), p["name"], p["clinic"], re.sub(r"^For [A-Za-z ]+: ", "", fl), srcs, p["contact_source"], p.get("decision") or ""]))
    for g in res.get("general") or []:
        erin.append((4, ["Owen", "(not placed)", _privacy.clean_clauses(g["text"])[0], g["reason"], g["source"], "", ""]))
    erin.append((N, ["", "", "", "Check by hand: compare clinic names against the invoices. The tool can't tell who is already a customer. Owen phones existing customers."]))
    # This week
    unsent = [r for r in wanted if r["body"] and not r["status"].startswith(("ALREADY", "NO DRAFT", "HOLD", "PRIVACY"))]
    open_flags = sum(1 for r in wanted if r["status"].startswith("WAITING"))
    week = [(T, ["This week: what still hasn't happened"]), (N, [f"{len(unsent)} people still to be written to or phoned. {open_flags} waiting on a decision. Sent mail shows up after Erin adds the cc'd mail to the activity file and runs again."]),
            (H, ["#", "Person", "Clinic", "From", "Next step", "Status"])]
    for r in unsent:
        week.append((N, [r["send_order"], r["name"], r["clinic"], r["sender"], r["next_step"], r["status"]]))
    held = [r for r in wanted if r["status"].startswith(("NO DRAFT", "HOLD", "PRIVACY"))]
    if held:
        week.append((H, ["", "Held, no draft", "Clinic", "", "", "Why"]))
        for r in held: week.append((N, ["", r["name"], r["clinic"], "", "", r["status"].replace("NO DRAFT: ", "")]))
    # Day 30
    day = [(T, [f"{show_name}: 30 days later"]), (N, [f"{len(real)} real conversations. A demo counts once it's booked, even if it hasn't happened. This can't say who became a paying clinic. Same layout every show."]),
           (H, ["Pile", "Count", "", ""])]
    for pile in PILES: day.append((N, [pile, sum(1 for p in real if p.get("pile") == pile)]))
    day.append((N, []))
    day.append((H, ["Pile", "Person", "Clinic", "Why it's in this pile"]))
    for pile in PILES:
        for p in sorted((x for x in real if x.get("pile") == pile), key=lambda x: x["name"]):
            day.append((N, [pile, p["name"], p["clinic"], p.get("pile_evidence", "")]))
    # People
    people = [(H, ["Person", "Clinic", "City", "Clinics", "System", "Priority", "Next step", "Why", "From", "Language", "Email", "Contact came from", "Booth detail", "Records", "Day 30"])]
    for p in real:
        srcs = "; ".join(sorted({x["id"] for x in p["records"]} | {n["source"] for n in p["notes"]}))
        people.append((N, [p["name"], p["clinic"], p["city"], p["locations"] or "", p["system"], p["priority"], p["next_step"], p["why"], p["sender"], "French" if p["french"] else "English", p["email"], p["contact_source"], p.get("safe_detail", ""), srcs, p.get("pile") or ""]))
    # Start here
    cols = next((w for w in res["warnings"] if w.startswith("COLUMN")), "")
    warns = [w for w in res["warnings"] if not w.startswith("COLUMN")]
    start = [(T, [show_name]), (H, ["Check this first", ""]),
             (N, ["Real conversations", f"{len(real)} of {len(res['people'])} people"]),
             (N, ["Files read", f"{len(res['scans'])} scans, {len(res['cards'])} cards, {len(res['voices'])} voice notes, {len(res['lines'])} list lines, {len(res['activity'])} activity rows"]),
             (N, ["Columns used", cols.replace("COLUMN CHECK (read this first): ", "")]),
             (N, ["Ready or phone", f"{sum(1 for r in wanted if r['status'].startswith(('READY','CALL')))}"]),
             (N, ["Waiting on a decision", f"{open_flags}"]),
             (N, ["Held, no draft", f"{len(held)}"])]
    for w in warns: start.append((4, ["Warning", w]))
    start += [(N, []), (H, ["Who opens what", ""]), (N, ["Owen", "Owen tab, on his phone"]), (N, ["Erin", "Erin tab, then This week"]), (N, ["Nadia", "Nadia tab, This week, then Day 30"])]
    tabs = [("Start here", start, [24, 90], None), ("Owen", owen, [5, 22, 20, 24, 30, 26, 70, 38, 12], 3), ("Nadia", nadia, [5, 22, 20, 24, 30, 26, 70, 38, 12], 3),
            ("Erin", erin, [14, 22, 26, 62, 20, 22, 12], 3), ("This week", week, [5, 24, 28, 9, 14, 44], 3), ("Day 30", day, [30, 24, 34, 60], None), ("People", people, [22, 28, 14, 7, 11, 8, 13, 34, 8, 9, 34, 22, 60, 24, 26], 1)]
    z = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
    z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>' + "".join(f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(len(tabs))) + "</Types>")
    z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + "".join(f'<sheet name="{n}" sheetId="{i+1}" r:id="rId{i+1}"/>' for i, (n, *_ ) in enumerate(tabs)) + "</sheets></workbook>")
    z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i+1}.xml"/>' for i in range(len(tabs))) + f'<Relationship Id="rId{len(tabs)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
    z.writestr("xl/styles.xml", STYLES)
    for i, (n, data, widths, fr) in enumerate(tabs):
        z.writestr(f"xl/worksheets/sheet{i+1}.xml", sheet_xml(data, widths, fr))
    z.close()
