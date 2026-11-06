"""One page, three buttons. Each view answers one question, with the detail behind a tap.
Owen: who do I send tonight, in what order?  Nadia: what's mine, and how did the show do?
Erin: what do I check before anything goes out?"""
import html, json, re, urllib.parse
import drafts as _d, sandbar as _s

CSS = """
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font:17px/1.5 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#1d2326;background:#f7f6f2}
header{padding:10px 16px;font-size:13px;color:#6b7378;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}header a{color:#6b7378}
nav{display:flex;gap:8px;padding:0 16px 12px;position:sticky;top:0;background:#f7f6f2;z-index:2}
nav button{flex:1;padding:14px 8px;font-size:17px;font-weight:600;border:1.5px solid #1d2326;background:#fff;border-radius:10px;cursor:pointer;color:#1d2326}
nav button.on{background:#1d2326;color:#fff}
main{padding:4px 16px 48px;max-width:720px;margin:0 auto}.view{display:none}.view.on{display:block}
.lead{font-size:26px;font-weight:700;line-height:1.25;margin:12px 0 4px}.sub{color:#6b7378;font-size:15px;margin:0 0 16px}
h2{font-size:14px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:#6b7378;margin:26px 0 8px}
.row{background:#fff;border:1px solid #e3e1db;border-radius:12px;margin:6px 0;overflow:hidden}.row.todo{border-left:5px solid #f0c24b}
.hd{display:flex;align-items:center;gap:10px;padding:12px 14px;cursor:pointer}.hd.flat{cursor:default}
.hd .n{width:26px;color:#9aa1a6;font-size:14px;flex:none}.hd b{font-size:17px}.hd .c{color:#6b7378;font-size:14px}
.hd .grow{flex:1;min-width:0}.hd .step{font-size:13px;color:#6b7378;white-space:nowrap}
.bd{display:none;padding:0 14px 14px;border-top:1px solid #efede8}.row.open .bd{display:block}
.draft{white-space:pre-wrap;background:#faf9f5;border-radius:8px;padding:12px;margin:12px 0 10px;font-size:16px}.draft mark{background:#fff0b3;padding:0 3px;border-radius:3px}
.meta{font-size:13px;color:#6b7378;margin:6px 0;overflow-wrap:anywhere}
.act{display:inline-block;padding:10px 16px;border:1.5px solid #1d2326;background:#1d2326;color:#fff;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;margin:4px 8px 4px 0;text-decoration:none}
.alt{background:#fff;color:#1d2326}.act.done{background:#2f8f5b;border-color:#2f8f5b;color:#fff}.pick{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.nums{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:8px 0 4px}.nums div{background:#fff;border:1px solid #e3e1db;border-radius:12px;padding:12px 8px;text-align:center}
.nums b{display:block;font-size:30px;line-height:1.1}.nums span{font-size:12px;color:#6b7378;display:block;margin-top:4px}
.chk{display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-bottom:1px solid #e3e1db;font-size:16px}.chk input{width:22px;height:22px;margin-top:2px;flex:none}
.why{font-size:13px;color:#6b7378}details.more{margin:10px 0}details.more summary{cursor:pointer;color:#6b7378;font-size:14px}
input.search{width:100%;padding:12px 14px;font-size:17px;border:1.5px solid #c9c6bf;border-radius:10px;margin:6px 0 10px}
.hit{padding:10px 0;border-bottom:1px solid #e3e1db;font-size:15px}.warn{background:#fff6d6;border:1px solid #f0c24b;border-radius:10px;padding:10px 14px;font-size:15px;margin:8px 0}
.tag{font-size:13px;font-weight:600;color:#1d2326;margin-top:2px}.todoline{font-size:14px;font-weight:600;color:#1d2326;margin-top:4px}
.stop{background:#fde8e6;border-color:#d9534f}.empty{color:#6b7378;font-style:italic}.dl a{display:block;padding:6px 0;color:#1d2326}
@media(max-width:420px){.nums{grid-template-columns:repeat(2,1fr)}.lead{font-size:23px}}
"""
JS = """
var live=location.protocol.indexOf('http')==0;
function ls(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}catch(e){return null}}
function show(v){document.querySelectorAll('.view').forEach(function(e){e.classList.toggle('on',e.id==v)});document.querySelectorAll('nav button').forEach(function(b){b.classList.toggle('on',b.dataset.v==v)});ls('sb_view',v);window.scrollTo(0,0)}
function tg(el){el.parentElement.classList.toggle('open')}
function cp(id,btn){var t=document.getElementById(id).innerText;function ok(){btn.textContent='Copied';btn.classList.add('done');ls('sb_done_'+id,'1')}
 if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(ok)}else{var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();ok()}}
function decide(btn){var k=btn.dataset;if(live&&k.show){btn.textContent='Saving…';fetch('/decide',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({show:k.show,person:k.person,clinic:k.clinic,decision:k.decision,by:k.by})}).then(function(r){if(r.ok)location.reload();else btn.textContent='Could not save'})}
 else{ls('sb_mark_'+k.person+k.clinic,k.decision);btn.parentElement.querySelectorAll('button').forEach(function(b){b.classList.remove('done')});btn.classList.add('done');var n=btn.parentElement.parentElement.querySelector('.tell');if(n)n.style.display='block'}}
function filt(q){q=q.toLowerCase();document.querySelectorAll('.hit[data-k]').forEach(function(h){h.style.display=(!q||h.dataset.k.indexOf(q)>=0)?'':'none'});document.getElementById('hits').style.display=q?'':'none'}
document.addEventListener('DOMContentLoaded',function(){if(live){var b=document.getElementById('back');if(b)b.style.display='inline'}
 show(ls('sb_view')||'owen');document.querySelectorAll('button.copy').forEach(function(b){if(ls('sb_done_'+b.dataset.id)){b.textContent='Copied';b.classList.add('done')}});
 document.querySelectorAll('.pick button').forEach(function(b){if(ls('sb_mark_'+b.dataset.person+b.dataset.clinic)==b.dataset.decision)b.classList.add('done')})});
"""
def e(s): return html.escape(str(s if s is not None else ""), quote=True)
def draft_html(t):
    t = e(t)
    for m in _d.PLACE.values(): t = t.replace(m, f"<mark>{m}</mark>")
    return t
def owner(fl):
    m = re.match(r"For ([A-Za-z ]+):", fl)
    return m.group(1) if m else ("Owen" if "Owen to" in fl else "Erin")
def bare(fl): return re.sub(r"^For [A-Za-z ]+: ", "", fl)

def render(res, got, show, when, path, memory_path=None):
    real, rows, people = res["real"], res["drafts"], res["people"]
    slug = re.sub(r".*/shows/", "", path).split("/")[0] if "/shows/" in path else ""
    def pick(p, options, by):
        d = (p.get("decision") or "").lower()
        b = "".join(f"<button class='act alt{' done' if d == v.lower() else ''}' onclick='decide(this)' data-show='{e(slug)}' data-person='{e(p['name'])}' data-clinic='{e(p['clinic'])}' data-decision='{e(v)}' data-by='{by}'>{e(l)}</button>" for l, v in options)
        tell = "" if slug else "<p class='why tell' style='display:none'>Marked on this device only. Tell Erin so the next run keeps it.</p>"
        return f"<div class='bd'><div class='pick'>{b}</div>{tell}</div>"
    missing = sorted({k for k, v in _d.PLACE.items() if any(v in (r.get("body") or "") + (r.get("cc") or "") for r in rows)})
    warn = f"<div class='warn'>Links not set yet: {e(', '.join(m.replace('_', ' ') for m in missing))}. Erin fills these once on the upload page and runs again.</div>" if missing else ""
    uid = [0]
    def send_row(r, i):
        uid[0] += 1; did = f"dr{uid[0]}"; p = r["p"]
        url = "mailto:" + urllib.parse.quote(r["to"] or "") + "?" + urllib.parse.urlencode({"cc": r["cc"], "subject": r["subject"], "body": r["body"]}, quote_via=urllib.parse.quote)
        notes = f"<p class='why'>⚑ {e(r['check'])}</p>" if r.get("check") else ""
        body = f"<div class='meta'>To: {e(r['to'] or 'no address')} · cc {e(r['cc'])}<br>Subject: {e(r['subject'])}</div><div class='draft' id='{did}'>{draft_html(r['body'])}</div>" \
               f"<button class='act copy' data-id='{did}' onclick=\"cp('{did}',this)\">Copy</button><a class='act alt' href='{e(url)}'>Open in my mail</a>{notes}"
        return (f"<div class='row{' todo' if r['status'].startswith('WAITING') else ''}'><div class='hd' onclick='tg(this)'><span class='n'>{i}</span><span class='grow'><b>{e(_d.greeting(p))}</b> <span class='c'>· {e(r['clinic'])}</span></span>"
                f"<span class='step'>{e(r['next_step'])}</span></div><div class='bd'>{body}</div></div>")
    def call_rows(rs):
        out = ""
        for r in rs:
            p = r["p"]; why = p.get("call_instead") or next((x for x in (r.get("check") or "").split(" | ") if x.startswith("Reminder")), "Call back.")
            ph = f" · {e(p.get('phone'))}" if p.get("phone") else ""
            out += f"<div class='row'><div class='hd flat'><span class='grow'><b>{e(_d.greeting(p))}</b> <span class='c'>· {e(r['clinic'])}{ph}</span><div class='why'>{e(why)}</div></span></div></div>"
        return out
    def is_ready(r): return r["status"].startswith("READY") and r["body"]
    def is_wait(r): return r["status"].startswith("WAITING") and r["body"]
    def is_call(r): return r["status"].startswith("CALL")
    def done(r): return r["status"].startswith(("ALREADY WRITTEN", "ALREADY BOOKED"))
    def nodraft(r): return r["status"].startswith(("NO DRAFT", "HOLD", "PRIVACY"))
    def mine(who): return [r for r in rows if r["sender"] == who]
    late_generic = [r for r in rows if "three weeks" in r["status"]]
    # ---------- Owen
    ow = mine("Owen"); send = [r for r in ow if is_ready(r)]; calls = [r for r in ow if is_call(r)]
    promised = sum(1 for r in send if r["p"]["first_batch"])
    o = f"<p class='lead'>{len(send)} to send</p><p class='sub'>{promised} promises first, then by size. Read, fix a word, send from your own mailbox, cc hello.</p>{warn}"
    o += "<h2>Send</h2>" + ("".join(send_row(r, i) for i, r in enumerate(send, 1)) or "<p class='empty'>Nothing ready.</p>")
    if calls: o += f"<h2>Call ({len(calls)})</h2>" + call_rows(calls)
    owaits = [(r, f) for r in rows for f in r["p"]["flags"] if owner(f) in ("Owen", "Owen and Nadia") and is_wait(r)]
    if owaits:
        o += f"<h2>Decide first ({len(owaits)})</h2><p class='sub'>Each waits alone. Everyone else is ready.</p>"
        for r, f in owaits:
            opts = [("Owen sends", "Owen"), ("Nadia sends", "Nadia")] if owner(f) == "Owen and Nadia" else [("Looks right", "OK"), ("Don't send", "Hold")]
            o += f"<div class='row todo'><div class='hd' onclick='tg(this)'><span class='grow'><b>{e(r['name'])}</b> <span class='c'>· {e(r['clinic'])}</span><div class='why'>{e(bare(f))}</div></span></div>{pick(r['p'], opts, 'Owen')}</div>"
    if res["general"]:
        o += f"<h2>Lines the tool can't place ({len(res['general'])})</h2>" + "".join(f"<div class='row todo'><div class='hd flat'><span class='grow'><b>{e(_s.clean_text(g['text']))}</b><div class='why'>{e(g['source'])}: {e(g['reason'])}</div></span></div></div>" for g in res["general"])
    gone = [r for r in ow if done(r)]
    if gone: o += f"<details class='more'><summary>Already handled ({len(gone)})</summary>" + "".join(f"<div class='hit'><b>{e(r['name'])}</b> · {e(r['status'])}</div>" for r in gone) + "</details>"
    skip = [r for r in ow if nodraft(r)]
    if skip: o += f"<details class='more'><summary>Not drafted on purpose ({len(skip)})</summary>" + "".join(f"<div class='hit'><b>{e(r['name'])}</b> · {e(r['status'].replace('NO DRAFT: ', ''))}</div>" for r in skip) + "</details>"
    # ---------- Nadia
    have = any(p.get("sent") or p.get("pile") in ("booked a demo", "started a trial") for p in real) or bool(res.get("had_activity"))
    PILES = _d.PILES; LAB = ["demos", "trials", "written, nothing yet", "never written"]
    nsend = [r for r in mine("Nadia") if is_ready(r)]; ncalls = [r for r in mine("Nadia") if is_call(r)]
    claims = [r for r in rows if any("Was this you" in f for f in r["p"]["flags"]) and not nodraft(r) and not r["p"].get("decided")]
    n = f"<p class='lead'>{e(show)}: {len(real)} real conversations</p>"
    n += "<p class='sub'>Every one in one of four piles. Same shape every show, so shows sit side by side.</p>" if have else "<p class='sub'>The four piles fill in once Erin adds the after-show activity, around day 30.</p>"
    n += "<div class='nums'>" + "".join(f"<div><b>{sum(1 for p in real if p.get('pile') == k) if have else '–'}</b><span>{l}</span></div>" for k, l in zip(PILES, LAB)) + "</div>"
    if have:
        n += "<details class='more'><summary>Names behind each pile</summary>"
        for k in PILES:
            items = sorted((p for p in real if p.get("pile") == k), key=lambda x: x["name"])
            n += f"<p class='why'><b>{e(k)} ({len(items)})</b><br>" + ("<br>".join(f"{e(p['name'])}, {e(p['clinic'])}" + (f" <i>({e(p.get('pile_evidence'))})</i>" if k in PILES[:2] else "") for p in items) or "—") + "</p>"
        n += "<p class='why'>This can't say who became a paying clinic. <a href='day30_page.html'>Printable page</a></p></details>"
    n += warn + f"<h2>Your drafts ({len(nsend)})</h2><p class='sub'>Send from your own mailbox, cc hello.</p>" + ("".join(send_row(r, i) for i, r in enumerate(nsend, 1)) or "<p class='empty'>None ready.</p>")
    if ncalls: n += f"<h2>Call ({len(ncalls)})</h2>" + call_rows(ncalls)
    if claims:
        n += f"<h2>Was this you? ({len(claims)})</h2><p class='sub'>Scanned on your phone, nothing else. Nothing goes out under your name until you claim it.</p>"
        for r in claims:
            note = r["p"].get("safe_detail", "")
            n += f"<div class='row todo'><div class='hd' onclick='tg(this)'><span class='grow'><b>{e(r['name'])}</b> <span class='c'>· {e(r['clinic'])}</span><div class='why'>{e(note)}</div></span></div>{pick(r['p'], [('Mine', 'Mine'), ('Pass to Owen', 'Owen')], 'Nadia')}</div>"
    both = [(r, f) for r in rows for f in r["p"]["flags"] if owner(f) == "Owen and Nadia" and is_wait(r)]
    if both:
        n += f"<h2>Decide with Owen ({len(both)})</h2>" + "".join(f"<div class='row todo'><div class='hd' onclick='tg(this)'><span class='grow'><b>{e(r['name'])}</b> <span class='c'>· {e(r['clinic'])}</span><div class='why'>{e(bare(f))}</div></span></div>{pick(r['p'], [('Owen sends', 'Owen'), ('I send', 'Nadia')], 'Nadia')}</div>" for r, f in both)
    nf = [(r, f) for r in rows for f in r["p"]["flags"] if owner(f) == "Nadia" and "Was this you" not in f]
    if nf: n += f"<h2>Also for you ({len(nf)})</h2>" + "".join(f"<div class='row todo'><div class='hd flat'><span class='grow'><b>{e(r['name'])}</b><div class='why'>{e(bare(f))}</div></span></div></div>" for r, f in nf)
    open_n = sum(1 for r in rows if is_wait(r)); unsent = sum(1 for r in rows if is_ready(r))
    n += "<h2>Your checks</h2>"
    for t in [f"Export, Owen's notes and your cards reached Erin ({len(res.get('scans', []))} scans, {len(res.get('cards', []))} cards, {len(res.get('voices', []))} voice notes)", f"End of week: {unsent} unsent, {open_n} decisions open", "Day 30: read the piles before Sam asks", "Legal answer on the N-flag people"]:
        n += f"<label class='chk'><input type='checkbox'>{e(t)}</label>"
    # ---------- Erin: not a follow-up list. She checks the data, hands questions to whoever can answer them, and passes the rest on.
    def cat(text):
        """Who answers, what kind of question, what to do. Never guesses the answer for them."""
        t = text.lower()
        if "both wrote" in t or "decide who sends" in t: return "Who sends", "One of them sends"
        if "was this you" in t: return "Who sends", "Nadia claims it or passes it on"
        if "source conflict" in t or "sources differ" in t: return "Needs confirmation", "Confirm the next step"
        if "no longer want" in t: return "Needs confirmation", "Check the draft"
        if "placed by a guess" in t: return "Identity unclear", "Owen confirms who"
        if "specific document" in t or "check it exists" in t: return "Needs confirmation", "Check the document exists"
        if "bounced" in t: return "Needs confirmation", "Owen checks the address"
        return "Needs confirmation", "Confirm or correct"
    def check_action(text):
        t = text.lower()
        if "identity unsure" in t: return "Same person or Different person"
        if "legal review" in t or "share flag n" in t or "consent = n" in t: return "Hold. Nadia asks someone who knows the law"
        if "do-not-email" in t or "asked to be removed" in t or "withdrew" in t: return "Nothing to send"
        if "bounced" in t: return "Find an address, or Owen phones"
        if "customer" in t: return "Check the invoices. Owen phones"
        if "no usable email address and no phone" in t or "no name" in t: return "Find a contact"
        if "no usable email" in t: return "Find an address. Until then, a call"
        if "isn't usable" in t: return "Check the address"
        if "consent" in t: return "Check the badge"
        if "only one name" in t: return "Check the full name"
        if "date" in t or "window" in t or "before the show" in t or "cancelled" in t: return "Check the date"
        if "already in touch" in t: return "Ask Owen"
        return "Done or Hold"
    held = [r for r in rows if nodraft(r) and "three weeks" not in r["status"]]
    ef = [(r, f) for r in rows for f in r["p"]["flags"] if owner(f) == "Erin" and not (r["p"].get("hold") and f == r["p"]["hold"]) and not r["p"].get("decided") and "source conflict" not in f.lower() and not r["p"].get("legal_hold") and not r["p"].get("dne")]
    allissues = res.get("issues", []) + got.get("issues", [])
    stop = [w for w in res["warnings"] if "Memory file" in w or "No memory" in w or w.startswith("Stop:")]
    other = [w for w in res["warnings"] if w not in stop and not w.startswith("COLUMN CHECK")]
    col = next((w for w in res["warnings"] if w.startswith("COLUMN CHECK")), "")
    # 1. what needs her, and links
    r_ = f"<p class='lead'>{len(ef) + len(held) + len(allissues)} to check</p><p class='sub'>Before anything goes to Owen's phone.</p>"
    r_ += "".join(f"<div class='warn stop'><b>Stop.</b> {e(w)}</div>" for w in stop) + warn
    # 2. this run
    drafts_n = sum(1 for r in rows if r["body"] and not done(r)); ready_n = sum(1 for r in rows if is_ready(r)); wait_n = sum(1 for r in rows if is_wait(r)); flags_n = sum(len(r["p"]["flags"]) for r in rows) + len(res["general"])
    dropped = sum(len(p.get("private_raw", [])) for p in people); removed = len(res.get("removal", []))
    r_ += "<h2>This run</h2><div class='row'><div class='hd flat'><span class='grow'>"
    r_ += f"{len(res.get('scans', []))} scans · {len(res.get('cards', []))} cards · {len(res.get('voices', []))} voice notes · {len(res.get('lines', []))} list lines<br>"
    r_ += f"<b>{len(real)}</b> real conversations · {len(people) - len(real)} excluded · <b>{drafts_n}</b> draft{'' if drafts_n == 1 else 's'} ({ready_n} ready, {wait_n} waiting on a decision) · {sum(1 for r in rows if is_call(r))} to call · {len(held)} held · {flags_n} flag{'' if flags_n == 1 else 's'}"
    r_ += f"<div class='why'>{dropped} personal remark{'' if dropped == 1 else 's'} kept out · {removed} asked to be removed → memory.csv<br>Run as of {when.strftime('%Y-%m-%d')} · {e('; '.join(got['used']) or 'none')}"
    if got["ignored"]: r_ += f"<br>Ignored: {e('; '.join(got['ignored']))}"
    r_ += "</div></span></div></div>"
    if late_generic or other:
        r_ += f"<details class='more'><summary>Notes on this run ({len(other) + (1 if late_generic else 0)})</summary>" + "".join(f"<p class='why'>{e(w)}</p>" for w in other)
        if late_generic: r_ += f"<p class='why'>{len(late_generic)} generic thank-yous not drafted: more than three weeks after the show on the run date. Promises are still drafted.</p>"
        r_ += "</details>"
    # 3. CHECK: hers
    r_ += f"<h2>Check ({len(ef) + len(held) + len(allissues)})</h2><p class='sub'>Do these first.</p>"
    def chk(name, clinic, why, action, extra="", todo=True):
        c = "<span class='c'>· " + e(clinic) + "</span>" if clinic else ""
        return f"<div class='row{' todo' if todo else ''}'><div class='hd{'' if extra else ' flat'}' {'onclick=tg(this)' if extra else ''}><span class='grow'><b>{e(name)}</b> {c}<div class='why'>{e(why)}</div><div class='todoline'>Action: {e(action)}</div></span></div>{extra}</div>"
    def brief(why):
        t = why.lower()
        if "legal review" in t:
            m = re.search(r"asked for (\w[\w -]*?) at the booth", why)
            return "badge says N" + (f"; asked for {m.group(1)}" if m else "") + ("; handed a card" if "with a card" in t else "")
        if "identity unsure" in t:
            m = re.search(r"may be ([^,]+),", why); return f"might be {m.group(1) if m else 'someone'} who asked off. Same person?"
        if "do-not-email" in t or "asked to be removed" in t: return "asked to be removed"
        if "withdrew" in t: return "withdrew permission"
        if "bounced" in t: return re.sub(r"^Only address bounced \(([^)]+)\)\..*", r"\1 bounced, no other address", why)
        if "no usable email address and no phone" in t: return "no email, no phone"
        if "no usable email" in t: return "no usable email"
        if "existing customer" in t: return "existing customer"
        if "already in touch" in t: return "already in touch"
        if "no name" in t: return "no name on the record"
        return why[:90]
    for r in held:
        why = brief(r["status"].replace("NO DRAFT: ", ""))
        extra = pick(r["p"], [("Same person", "Same"), ("Different person", "Different")], "Erin") if r["p"].get("dne_suspected") else ""
        r_ += chk(r["name"], r["clinic"], why, check_action(r["status"]), extra)
    for r, f in ef:
        if r["p"].get("legal_hold") or r["p"].get("dne"): continue  # already held above
        txt = bare(f).split(". ")[0].rstrip(".")
        txt = re.sub(r": reply with.*$", "", txt)
        r_ += chk(r["name"], r["clinic"], txt, check_action(f), pick(r["p"], [("Done", "OK"), ("Hold", "Hold")], "Erin"))
    for i in allissues:
        r_ += chk(i["file"], i["record"], i["reason"], check_action(i["reason"]) if "date" in i["reason"].lower() else "Look at the record")
    if not (held or ef or allissues): r_ += "<p class='empty'>Nothing for you this run.</p>"
    r_ += "<p class='why'>Also check clinic names against the invoices.</p>"
    # 4. FLAGS: someone else's answer. She passes it on; she doesn't guess it.
    claims_e = [r for r in rows if any("Was this you" in f for f in r["p"]["flags"]) and not nodraft(r) and not r["p"].get("decided")]
    fl = []
    for r in rows:
        for f in r["p"]["flags"]:
            who = owner(f)
            if "source conflict" in f.lower(): who = r["sender"]
            if who == "Erin" or "Was this you" in f or nodraft(r) or (r["p"].get("decided") and who != "Owen"): continue
            kind, act = cat(f)
            txt = bare(f).split(". ")[0].rstrip("."); txt = re.sub(r";.*$", "", txt); fl.append((who, r["name"], r["clinic"], kind, txt[:1].upper() + txt[1:], act))
    for g in res["general"]:
        t = _s.clean_text(g["text"])
        fl.append(("Owen", g["source"], (t[:40] + "…") if len(t) > 40 else t, "Identity unclear", g["reason"].split(". ")[0], "Owen says who this is"))
    total_flags = len(fl) + (1 if claims_e else 0)
    r_ += f"<h2>Flags ({total_flags}): Owen or Nadia</h2><p class='sub'>Pass each one on.</p>"
    for who, name, clinic, kind, why, act in fl:
        r_ += f"<div class='row'><div class='hd flat'><span class='grow'><b>{e(name)}</b> <span class='c'>{('· ' + e(clinic)) if clinic else ''}</span><div class='tag'>{e(who)} · {e(kind)}</div><div class='why'>{e(why)}</div><div class='todoline'>Action: {e(act)}</div></span></div></div>"
    if claims_e:
        r_ += f"<div class='row'><div class='hd flat'><span class='grow'><b>{len(claims_e)} scans from Nadia's phone</b><div class='tag'>Nadia · Who sends</div><div class='why'>On her page under Was this you?</div><div class='todoline'>Action: Remind Nadia</div></span></div></div>"
    if not total_flags: r_ += "<p class='empty'>Nothing waiting on them.</p>"
    # 5. Ready: theirs to send, from their own mailbox
    o_ready = sum(1 for r in mine("Owen") if is_ready(r)); n_ready = sum(1 for r in mine("Nadia") if is_ready(r))
    o_call = sum(1 for r in mine("Owen") if is_call(r)); n_call = sum(1 for r in mine("Nadia") if is_call(r))
    r_ += "<h2>Ready for follow-up</h2><div class='row'><div class='hd flat'><span class='grow'>"
    r_ += f"<b>Owen</b>: {o_ready} ready, {o_call} to call · <b>Nadia</b>: {n_ready} ready, {n_call} to call"
    r_ += "<div class='why'>Sent by whoever had the conversation, cc hello.</div><div class='todoline'>Action: Put the page and Sheet in the Drive folder, tell them</div></span></div></div>"
    # 6. Excluded: folded
    excl = [p for p in people if not p["real"]]
    r_ += f"<details class='more'><summary>Excluded, no email ({len(excl)})</summary>" + "".join(f"<div class='hit'><b>{e(p['name'] or '(no name)')}</b>{(' · ' + e(p['clinic'])) if p['clinic'] else ''}<br><span class='why'>{e(p['real_why'])}</span></div>" for p in excl) + "</details>"
    # 7. Look up
    r_ += "<h2>Look up anyone</h2><input class='search' placeholder='Name or clinic' oninput='filt(this.value)'><div id='hits' style='display:none'>"
    st = {id(r["p"]): r["status"] for r in rows}
    for p in people:
        k = e((p["name"] + " " + p["clinic"]).lower()); src = "; ".join(sorted({x["id"] for x in p["records"]} | {x["source"] for x in p["notes"]}))
        if p["real"]:
            r_ += f"<div class='hit' data-k='{k}'><b>{e(p['name'])}</b> · {e(p['clinic'])}<br><span class='why'>{e(p['priority'])}: {e(p['why'])} Next step {e(p['next_step'])}, from {e(p['sender'])}. {e(st.get(id(p), ''))} {('Pile: ' + e(p.get('pile')) + '.') if have else ''} {e(p.get('safe_detail'))} Sources {e(src)}.</span></div>"
        else:
            r_ += f"<div class='hit' data-k='{k}'><b>{e(p['name'])}</b> · {e(p['clinic'])}<br><span class='why'>Not a conversation: {e(p['real_why'])}. Sources {e(src)}.</span></div>"
    r_ += "</div>"
    if col: r_ += f"<details class='more'><summary>Columns used (check these if the organiser changed the export)</summary><p class='why'>{e(col.split(': ', 1)[-1])}</p></details>"
    r_ += "<h2>Files</h2><div class='dl'><a href='Sandbar_follow_up.xlsx'>Sandbar_follow_up.xlsx: the same thing as a Sheet, for the restricted Drive folder</a><a href='drafts.csv'>drafts.csv</a><a href='flags.csv'>flags.csv</a><a href='piles.csv'>piles.csv</a><a href='people.csv'>people.csv</a><a href='not_a_conversation.csv'>not_a_conversation.csv</a><a href='input_issues.csv'>input_issues.csv</a></div>"
    r_ += "<p class='why'>Rules with dates: rules.md · Steps: HOW-TO-RUN.md · Back up memory.csv to the restricted Drive folder after every run.</p>"
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sandbar: {e(show)}</title><style>{CSS}</style></head>
<body><header><span>Sandbar after-show station · {e(show)}</span><span><a id='back' href='/' style='display:none'>← New show</a> nothing is sent from here</span></header>
<nav><button data-v="nadia" onclick="show('nadia')">Nadia</button><button data-v="owen" onclick="show('owen')">Owen</button><button data-v="erin" onclick="show('erin')">Erin</button></nav>
<main><section id="nadia" class="view">{n}</section><section id="owen" class="view">{o}</section><section id="erin" class="view">{r_}</section></main>
<script>{JS}</script></body></html>"""
    with open(path, "w", encoding="utf-8") as f: f.write(doc)
