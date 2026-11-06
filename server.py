#!/usr/bin/env python3
"""The upload page. Double-click start.command (Mac) or start.bat (Windows); it opens
http://localhost:8765 in the browser. Erin names the show, drops the files, fills the
links once, presses Run. The tool runs run.py and opens the page. Nothing leaves the computer.

Python 3 only, no packages. Ctrl-C in the terminal window stops it.
"""
import csv, hashlib, html, json, os, re, shutil, subprocess, sys, webbrowser
from datetime import date, datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
SHOWS = os.path.join(HERE, "shows")
SETTINGS = os.path.join(HERE, "settings.json")
PORT = int(os.environ.get("SANDBAR_PORT", "8765"))

LINKS = [("demo_link", "Demo booking link (Nadia's calendar)"), ("trial_link", "Trial sign-up link"),
         ("one_pager", "One-pager link"), ("security_doc", "Security document link (leave empty if there isn't one: Owen calls instead)"),
         ("hello_address", "hello@ address to cc")]

CSS = """body{margin:0;font:17px/1.5 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#1d2326;background:#f7f6f2}
main{max-width:640px;margin:0 auto;padding:24px 16px 48px}h1{font-size:26px;margin:0 0 4px}.sub{color:#6b7378;margin:0 0 20px}
h2{font-size:14px;text-transform:uppercase;letter-spacing:.04em;color:#6b7378;margin:26px 0 8px}
label{display:block;margin:10px 0 4px;font-weight:600}small{display:block;color:#6b7378;font-weight:400}
input[type=text],input[type=date],input[type=url]{width:100%;padding:11px 12px;font-size:16px;border:1.5px solid #c9c6bf;border-radius:8px;box-sizing:border-box}
input[type=file]{font-size:15px;margin:4px 0}
.ok{color:#2f8f5b}.warn{background:#fff6d6;border:1px solid #f0c24b;border-radius:10px;padding:10px 14px;margin:8px 0}
button{padding:14px 24px;font-size:18px;font-weight:700;border:0;background:#1d2326;color:#fff;border-radius:10px;cursor:pointer;margin-top:20px}
a{color:#1d2326}.prev{background:#fff;border:1px solid #e3e1db;border-radius:12px;padding:12px 14px;margin:8px 0}
details{margin:10px 0}summary{cursor:pointer;color:#6b7378}
.two{display:grid;grid-template-columns:2fr 1fr;gap:12px}.two label{margin-top:0}
.drop{position:relative;margin:20px 0 4px;padding:36px 20px;border:2px dashed #b9b5ac;border-radius:16px;background:#fff;text-align:center;min-height:200px}
.drop.over{border-color:#1d2326;background:#fff6d6}.drop.has{border-style:solid;border-color:#2f8f5b}
.drop input{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:pointer}
.drop .big{font-size:22px;font-weight:700}.drop .small{color:#6b7378;font-size:14px;margin-top:8px;line-height:1.5}
.drop ul{list-style:none;padding:0;margin:14px 0 0;text-align:left;display:inline-block;position:relative;z-index:1;pointer-events:none}.drop li{padding:4px 0;font-size:16px}.drop li:before{content:'✓ ';color:#2f8f5b}
button:disabled{background:#b9b5ac;cursor:default}"""

def load_settings():
    try:
        with open(SETTINGS, encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def shows_done():
    out = []
    if os.path.isdir(SHOWS):
        for name in sorted(os.listdir(SHOWS)):
            if os.path.exists(os.path.join(SHOWS, name, "out", "index.html")):
                out.append(name)
    return out

MEMORY = os.path.join(HERE, "memory.csv")

def run_show(slug, show, today):
    folder = os.path.join(SHOWS, slug)
    cmd = [sys.executable, os.path.join(HERE, "run.py"), "--data", os.path.join(folder, "data"), "--out", os.path.join(folder, "out"),
           "--show", show, "--today", today, "--settings", SETTINGS, "--memory", MEMORY]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)

def page(body):
    return f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Sandbar: new show</title><style>{CSS}</style></head><body><main>{body}</main></body></html>"

def form_html(msg=""):
    s = load_settings()
    missing = [k for k, _ in LINKS if not s.get(k, "").strip()]
    prev = "".join(f"<div class='prev'><a href='/shows/{html.escape(n)}/out/index.html'><b>{html.escape(n)}</b></a> · <a href='/shows/{html.escape(n)}/out/'>files</a></div>" for n in shows_done())
    links = "".join(f"<label>{lab}</label><input type='text' name='{k}' value='{html.escape(s.get(k, ''))}' placeholder='https://…'>" for k, lab in LINKS)
    warn = f"<div class='warn'>Links not set yet: {', '.join(m.replace('_', ' ') for m in missing)}. Drafts show a yellow marker where the link goes until you fill them in below (once).</div>" if missing else ""
    return page(f"""
<h1>New show</h1><p class='sub'>Drop everything from the show in the box. The tool works out what each file is.</p>{msg}{warn}
<form method='post' action='/run' enctype='multipart/form-data' id='f'>
<label>Show</label><input type='text' name='show' required placeholder='Moncton'>
<div id='drop' class='drop'><input type='file' name='files' id='files' multiple accept='.csv,.xlsx,.json,.txt'>
<div class='big'>Drop the files here</div><div class='small'>scan export · cards · voice notes · Owen's list · after-show activity · already-sent list<br>CSV, Excel or JSON, any column names, one file or many, all at once</div>
<ul id='list'></ul></div>
<fieldset style='border:0;padding:0;margin:14px 0 0'><label><input type='radio' name='mode' value='replace' checked> <b>Replace</b> <small style='display:inline'>this show's files with these (normal)</small></label><label><input type='radio' name='mode' value='add'> <b>Add to</b> <small style='display:inline'>the files this show already has (late cards, cc'd mail, day 30)</small></label></fieldset>
<button type='submit' id='go' disabled>Run</button>
<details><summary>Links (fill once, kept for every show)</summary>{links}</details>
<details><summary>Run as of another day</summary><label>Run as of <small>normally today. A generic note more than three weeks after the show is not drafted (rule of Nov 2); promises never expire. Set a date near the show to rehearse or to see the first-week view.</small></label><input type='date' name='today' value='{date.today().isoformat()}'></details>
</form>
{'<h2>Earlier shows</h2>' + prev if prev else ''}
<p><small>Steps and rules: HOW-TO-RUN.md, rules.md in this folder. Nothing is sent from here.</small></p>
<script>
var inp=document.getElementById('files'),drop=document.getElementById('drop'),list=document.getElementById('list'),go=document.getElementById('go');
function showList(){{list.innerHTML='';for(var i=0;i<inp.files.length;i++){{var li=document.createElement('li');li.textContent=inp.files[i].name;list.appendChild(li)}};go.disabled=!inp.files.length;drop.classList.toggle('has',!!inp.files.length)}}
inp.addEventListener('change',showList);
['dragenter','dragover'].forEach(function(e){{drop.addEventListener(e,function(ev){{ev.preventDefault();drop.classList.add('over')}})}});
['dragleave','drop'].forEach(function(e){{drop.addEventListener(e,function(ev){{ev.preventDefault();drop.classList.remove('over')}})}});
drop.addEventListener('drop',function(ev){{var dt=new DataTransfer();for(var i=0;i<inp.files.length;i++)dt.items.add(inp.files[i]);for(var j=0;j<ev.dataTransfer.files.length;j++)dt.items.add(ev.dataTransfer.files[j]);inp.files=dt.files;showList()}});
</script>""")

def parse_multipart(body, ctype):
    """Minimal multipart/form-data parser (stdlib cgi is gone in Python 3.13). Returns {field: (filename or None, bytes)}."""
    m = re.search(r'boundary="?([^";]+)"?', ctype or "")
    out = {}
    if not m: return out
    bnd = b"--" + m.group(1).encode()
    for part in body.split(bnd)[1:]:
        if part.strip() in (b"", b"--"): continue
        if part.startswith(b"\r\n"): part = part[2:]
        head, _, data = part.partition(b"\r\n\r\n")
        if data.endswith(b"\r\n"): data = data[:-2]
        h = head.decode("utf-8", "replace")
        name = re.search(r'name="([^"]*)"', h); fn = re.search(r'filename="([^"]*)"', h)
        if name: out.setdefault(name.group(1), []).append((fn.group(1) if fn else None, data))
    return out

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, body, code=200, ctype="text/html; charset=utf-8"):
        if isinstance(body, str): body = body.encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body))); self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"):
            return self._send(form_html())
        if p.startswith("/shows/"):
            rel = os.path.normpath(p.lstrip("/"))
            if not rel.startswith("shows" + os.sep) or ".." in rel.split(os.sep): return self._send("no", 404)
            full = os.path.join(HERE, rel)
            if os.path.isdir(full):
                items = "".join(f"<div class='prev'><a href='/{rel}/{html.escape(n)}'>{html.escape(n)}</a></div>" for n in sorted(os.listdir(full)))
                return self._send(page(f"<h1>{html.escape(rel)}</h1><p><a href='/'>← new show</a></p>{items}"))
            if os.path.isfile(full):
                ctype = "text/html; charset=utf-8" if full.endswith(".html") else "text/csv; charset=utf-8" if full.endswith(".csv") else "application/json" if full.endswith(".json") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if full.endswith(".xlsx") else "text/plain; charset=utf-8"
                with open(full, "rb") as f: return self._send(f.read(), 200, ctype)
        return self._send(page("<h1>Not found</h1><p><a href='/'>← new show</a></p>"), 404)

    def do_POST(self):
        if self.headers.get("Host", "").split(":")[0] not in ("localhost", "127.0.0.1"):
            return self._send("no", 403)
        n = int(self.headers.get("Content-Length") or 0)
        if self.path == "/decide":
            return self.decide(self.rfile.read(n))
        if self.path != "/run":
            return self._send("no", 404)
        form = parse_multipart(self.rfile.read(n), self.headers.get("Content-Type", ""))
        def val(k): return form[k][0][1].decode("utf-8", "replace") if k in form and form[k][0][0] is None else None
        show = (val("show") or "").strip()
        today = (val("today") or date.today().isoformat()).strip()
        if not show:
            return self._send(form_html("<div class='warn'>Give the show a name.</div>"))
        slug = re.sub(r"[^A-Za-z0-9]+", "-", show).strip("-").lower() or "show"
        folder = os.path.join(SHOWS, slug); data = os.path.join(folder, "data"); out = os.path.join(folder, "out")
        mode = (val("mode") or "replace").strip()
        if not any(fn and blob for fn, blob in form.get("files", [])):
            return self._send(form_html("<div class='warn'>No files dropped.</div>"))
        if mode != "add" and os.path.isdir(data): shutil.rmtree(data)  # default: old files never mix silently into a new run
        os.makedirs(data, exist_ok=True); os.makedirs(out, exist_ok=True)
        # links: saved once, used for every show
        s = load_settings()
        for k, _ in LINKS:
            v = val(k)
            if v is not None: s[k] = v.strip()
        with open(SETTINGS, "w", encoding="utf-8") as f: json.dump(s, f, indent=2)
        # files: each saved under a fixed name so run.py finds them; the scan export keeps its own columns
        saved, seen, manifest = [], set(), []
        for fn, blob in form.get("files", []):
            if not fn or not blob: continue
            h = hash(blob)
            if h in seen: continue  # same file dropped twice
            seen.add(h)
            ext = os.path.splitext(fn)[1].lower()
            fname = re.sub(r"[^A-Za-z0-9._-]+", "-", os.path.basename(fn)) or ("file" + ext)
            with open(os.path.join(data, fname), "wb") as f: f.write(blob)
            saved.append(fname); manifest.append(dict(file=fname, bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest()[:16]))
        if not saved:
            return self._send(form_html("<div class='warn'>No files dropped.</div>"))
        with open(os.path.join(folder, "run.json"), "w", encoding="utf-8") as f: json.dump(dict(show=show, today=today), f)
        with open(os.path.join(folder, "runs.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(dict(ran_at=datetime.now().isoformat(timespec="seconds"), mode=mode, run_as_of=today, files_added=manifest, files_in_run=sorted(os.listdir(data)))) + "\n")
        r = run_show(slug, show, today)
        if r.returncode != 0 or not os.path.exists(os.path.join(out, "index.html")):
            return self._send(form_html(f"<div class='warn'><b>The run stopped.</b> Nothing was sent. Files kept in shows/{html.escape(slug)}/data. What it said:<pre style='white-space:pre-wrap'>{html.escape((r.stderr or r.stdout)[-1500:])}</pre></div>"))
        self.send_response(303); self.send_header("Location", f"/shows/{slug}/out/index.html"); self.end_headers()

    def decide(self, raw):
        """A button on the page: saved beside the show's results, then the show runs again so everyone sees it."""
        try:
            d = json.loads(raw); slug = d["show"]
            if not re.fullmatch(r"[a-z0-9-]+", slug) or d["decision"] not in ("OK", "Hold", "Mine", "Owen", "Nadia", "Same", "Different") or d["by"] not in ("Owen", "Nadia", "Erin"): raise ValueError
            folder = os.path.join(SHOWS, slug); meta = json.load(open(os.path.join(folder, "run.json"), encoding="utf-8"))
        except Exception:
            return self._send("no", 400)
        path = os.path.join(folder, "out", "decisions.csv")
        rows = list(csv.DictReader(open(path, encoding="utf-8-sig"))) if os.path.exists(path) else []
        rows = [x for x in rows if (x["person"], x["clinic"]) != (d["person"], d["clinic"])]
        rows.append(dict(person=d["person"], clinic=d["clinic"], decision=d["decision"], by=d["by"], date=date.today().isoformat()))
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["person", "clinic", "decision", "by", "date"]); w.writeheader(); w.writerows(rows)
        r = run_show(slug, meta["show"], meta["today"])
        return self._send("ok" if r.returncode == 0 else "failed", 200 if r.returncode == 0 else 500, "text/plain")

def main():
    os.makedirs(SHOWS, exist_ok=True)
    srv = HTTPServer(("127.0.0.1", PORT), H)
    url = f"http://localhost:{PORT}/"
    print(f"Sandbar station: {url}   (close this window to stop)")
    try: webbrowser.open(url)
    except Exception: pass
    try: srv.serve_forever()
    except KeyboardInterrupt: pass

if __name__ == "__main__":
    main()
