"""What the tool remembers between shows: who must never get email, and who we have met before."""
import csv, json, os, re
FIELDS = ["name", "email", "clinic", "show", "status", "date", "note"]

def load(path, warnings):
    if not path:
        warnings.append("No memory file: the tool can't see earlier shows, so someone who asked to be removed before could get a draft.")
        return []
    if not os.path.exists(path):
        warnings.append(f"Memory file not found ({os.path.basename(path)}): starting with no history. If this isn't the first show, stop and find it.")
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r.setdefault("status", "do not email"); r["status"] = r.get("status") or "do not email"
    return rows

def show_name(notes_path, dates):
    label = ""
    if notes_path:
        about = json.load(open(notes_path, encoding="utf-8")).get("about", "")
        m = re.search(r"from the (.+?) booth", about); label = m.group(1) if m else ""
        m = re.search(r"\(([^,()]+),", about); label = (label + " " + (m.group(1) if m else "")).strip()
    return (label or "Show") + (" " + max(dates)[:4] if dates else "")

def apply_seen(people, mem, show_key, match):
    earlier = [m for m in mem if m.get("show") != show_key and m.get("status") != "do not email"]
    for p in people:
        if not p["real"]: continue
        hit = match(p, earlier)
        if not hit: continue
        p["seen_before"] = hit
        msg = f"For Owen: met at {hit.get('show','an earlier show')} ({hit.get('status','')}): a warmer conversation."
        if hit.get("status") in ("booked a demo", "started a trial") and p["next_step"] in ("demo", "trial"):
            msg = f"For Owen: already {hit['status']} after {hit.get('show','an earlier show')}. Check before sending another link."
            p["already_before"] = hit["status"]
        if hit.get("status") == "held: N flag":
            msg = f"For Erin: held at {hit.get('show','an earlier show')} because of the N flag. New badge says {'N' if p['hold'] else 'Y'}."
        p["flags"].append(msg)

def save(path, mem, people, removal, show_key):
    rows = [m for m in mem if m.get("show") != show_key or m.get("status") == "do not email"]
    known = {(r.get("email") or "").lower() for r in rows if r.get("status") == "do not email"}
    for r in removal:
        if (r.get("email") or "").lower() not in known:
            rows.append(dict(name=r["name"], email=r["email"], clinic=r["clinic"], show=show_key, status="do not email", date=r["date"], note="asked to be removed"))
    for p in people:  # a known removal with a new address: the new address goes on the list too
        if p["real"] and p.get("dne"):
            for e in p["all_emails"]:
                if e.lower() not in known and e:
                    known.add(e.lower()); rows.append(dict(name=p["name"], email=e, clinic=p["clinic"], show=show_key, status="do not email", date="", note="same person as an earlier removal"))
    removed = {(r.get("email") or "").lower() for r in rows if r.get("status") == "do not email"}
    for p in people:
        if not p["real"] or any(e in removed for e in p["all_emails"]): continue
        status = p.get("pile") or "met"
        if p.get("legal_hold"): status = "held: N flag"
        rows.append(dict(name=p["name"], email=p["email"], clinic=p["clinic"], show=show_key, status=status, date="", note=""))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
