"""Change the files the way Friday might, and check the tool still runs and gives the same answers."""
import csv, json, os, re, shutil, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import sandbar
SRC = os.path.join(os.path.dirname(__file__), "..", "toronto")
def snapshot(res):
    return {tuple(sorted({r["id"] for r in p["records"]})): (p["priority"], p["next_step"], bool(p["hold"])) for p in res["real"]}
def fresh():
    d = tempfile.mkdtemp(); [shutil.copy(os.path.join(SRC, f), d) for f in os.listdir(SRC)]; return d
def run(d): return sandbar.run(d, tempfile.mkdtemp())
base = run(fresh()); bs = snapshot(base)
print(f"baseline: {len(base['real'])} people")
def compare(label, res, allow_missing=False):
    s = snapshot(res)
    changed = [(k, bs[k], s[k]) for k in s if k in bs and s[k] != bs[k]]
    print(f"{label}: {len(res['real'])} people, {len(changed)} changed, new groups {len([k for k in s if k not in bs])}")
    for c in changed[:12]: print("    ", c)
    for w in res["warnings"]:
        if not w.startswith("COLUMN"): print("     warn:", w)

# 1 renamed columns, shuffled column order
d = fresh(); p = os.path.join(d, "badge-scans.csv"); rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
ren = {"scan_id": "Badge ID", "scanned_at": "Capture Time", "scanned_by": "Captured By", "first_name": "First Name", "last_name": "Last Name", "title": "Job Title",
       "company": "Organization", "email": "Email Address", "phone": "Telephone", "city": "City", "province": "State/Province", "share_with_exhibitors": "Opt-In to Exhibitors", "rating": "Lead Rating", "notes": "Comments"}
cols = list(ren)[::-1]
with open(p, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow([ren[c] for c in cols]); [w.writerow([r[c] for c in cols]) for r in rows]
compare("renamed + reordered columns", run(d))
# 2 one full-name column, Yes/No flag
d = fresh(); p = os.path.join(d, "badge-scans.csv")
with open(p, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Lead ID", "Scanned By", "Full Name", "Title", "Company", "E-mail", "Mobile", "City", "Consent to share", "Rating", "Notes"])
    for r in rows: w.writerow([r["scan_id"], r["scanned_by"], f"{r['first_name']} {r['last_name']}", r["title"], r["company"], r["email"], r["phone"], r["city"], {"Y": "Yes", "N": "No"}[r["share_with_exhibitors"]], r["rating"], r["notes"]])
compare("full-name column, Yes/No", run(d))
# 3 missing pieces
j = json.load(open(os.path.join(SRC, "booth-notes.json"), encoding="utf-8"))
def with_notes(fn):
    d = fresh(); x = json.loads(json.dumps(j)); fn(x); json.dump(x, open(os.path.join(d, "booth-notes.json"), "w"), ensure_ascii=False); return d
compare("no Nadia cards", run(with_notes(lambda x: x.update(cards=[c for c in x["cards"] if c["collected_by"] != "Nadia"]))))
compare("no Owen list", run(with_notes(lambda x: x.update(owen_list={"lines": []}))))
compare("no voice notes", run(with_notes(lambda x: x.update(voice_notes=[]))))
d = fresh(); os.remove(os.path.join(d, "after-show-activity.csv")); compare("no activity file", run(d))
d = fresh(); os.remove(os.path.join(d, "booth-notes.json")); compare("scans only", run(d))
d = fresh(); os.remove(os.path.join(d, "badge-scans.csv")); compare("no scans", run(d))
# 4 every name and clinic word swapped: proves no person from Toronto is written into the code
all_text = {f: open(os.path.join(SRC, f), encoding="utf-8").read() for f in os.listdir(SRC)}
vocab = set()
for r in rows:
    vocab |= set(sandbar.words(r["first_name"])) | set(sandbar.words(r["last_name"])) | set(sandbar.clinic_key(r["company"]))
for c in j["cards"]:
    f, l = sandbar.split_name(c["name"]); vocab |= set(f.split()) | {l} | set(sandbar.clinic_key(c["clinic"]))
import random
nick = {n for g in sandbar.NICK for n in g}
keep = {"com", "example", "clinivo", "bookstead", "pracshift", "still", "water", "waters", "edge", "motion"} | nick
vocab = {v for v in vocab if len(v) > 2 and v not in keep}
rnd = random.Random(7)
mp = {w: "".join(rnd.choice("bcdfgjkmpqtvwxz") + rnd.choice("aeiou") for _ in range(4)) for w in sorted(vocab)}
pat = re.compile(r"(?<![a-z0-9])(" + "|".join(map(re.escape, sorted(mp, key=len, reverse=True))) + r")(?![a-z0-9])", re.I)
d = tempfile.mkdtemp()
for f, tx in all_text.items():
    tx = tx.replace("O'Brien", "OBrien")
    open(os.path.join(d, f), "w", encoding="utf-8").write(pat.sub(lambda m: mp[m.group(1).lower()], tx))
print("--- every name and clinic word replaced with nonsense ---")
res = run(d); s = snapshot(res)
ch = [(k, bs[k], s[k]) for k in s if k in bs and s[k] != bs[k]]
print(f"people {len(res['real'])} (was {len(base['real'])}), changed {len(ch)}, regrouped {len([k for k in s if k not in bs])}")
for c in ch: print("    ", c)
print("    regrouped:", [k for k in s if k not in bs], "lost:", [k for k in bs if k not in s])
# 5 nothing personal in the output
o = tempfile.mkdtemp(); sandbar.run(fresh(), o)
txt = open(os.path.join(o, "people.csv"), encoding="utf-8").read() + open(os.path.join(o, "flags.csv"), encoding="utf-8").read()
print("personal words in output:", re.findall(r"\b(hospital|dad|dog|hockey|kids|bow tie|Sam)\b", txt))
