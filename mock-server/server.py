#!/usr/bin/env python3
"""NIDO Campo mock server. Stdlib only, no install.

    python3 mock-server/server.py            # http://localhost:8080
    PORT=9000 python3 mock-server/server.py

Implements the campo/1 contract so the phone table can sync against it and the
board table can read a snapshot, even if the inbox table is not finished:

  GET  /api/campo/config                           -> config/<project>/project-config.json
  PUT  /api/campo/visits/{id}                      -> store visit JSON (idempotent by id)
  PUT  /api/campo/visits/{id}/media/{media_id}     -> store a file (idempotent by sha256)
  GET  /api/campo/visits/{id}                      -> what the server holds
  GET  /api/campo/visits                           -> list (newest first)
  POST /api/campo/visits/{id}/review               -> {"action": "approve_internal"|"approve_public"|"reject", "note": ""}
  GET  /api/transparency.json                      -> fixtures/transparency.json
  GET  /review                                     -> a tiny HTML inbox so you can see what arrived

Auth: Authorization: Bearer <project>:<invite-code>  (codes come from the config).
Data lands in mock-server/data/. Delete that folder to reset.
This is a MOCK: no auth beyond the code check, no TLS, no concurrency guarantees. The inbox
table replaces it; the contract stays the same.
"""
import hashlib, json, os, re, sys, time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = os.environ.get("PROJECT", "nido-pijao")
DATA = ROOT / "mock-server" / "data"
VISITS = DATA / "visits"
MEDIA = DATA / "media"
LEDGER = DATA / "ledger.jsonl"
for d in (VISITS, MEDIA):
    d.mkdir(parents=True, exist_ok=True)
CONFIG = json.loads((ROOT / "config" / PROJECT / "project-config.json").read_text(encoding="utf-8"))
CODES = set(CONFIG.get("invite_codes", {}).keys())
# seed the ledger from fixtures once
if not LEDGER.exists():
    LEDGER.write_text((ROOT / "fixtures" / "ledger.jsonl").read_text(encoding="utf-8"), encoding="utf-8")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(vid):
    f = VISITS / f"{vid}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def save(v):
    (VISITS / f"{v['id']}.json").write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")


def append_event(ev):
    ev.setdefault("id", f"evt_{int(time.time()*1000)}")
    ev.setdefault("at", now()[:10])
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def event_for(v):
    """Turn an approved visit into a ledger event (the inbox-to-board handoff)."""
    a = v.get("answers", {})
    t = v.get("visit_type")
    base = {"site": v.get("site_ref"), "source": f"campo:{v['id']}", "by": "review", "at": (v.get("ended_at") or v.get("started_at") or now())[:10]}
    if t == "minga":
        return dict(base, type="minga", attendees=a.get("attendees_count"), meals=a.get("meals"), meal_funder=a.get("meal_funder"))
    if t == "obra":
        return dict(base, type="step_progress", step=a.get("current_step"), progress_pct=int(a.get("step_progress") or 0))
    if t == "entrega":
        return dict(base, type="delivery", items=a.get("items"), signed=bool(a.get("signed_record")))
    return dict(base, type="milestone", text_es=f"Visita: {t}")


UUID = r"[0-9a-fA-F-]{8,64}"


class H(BaseHTTPRequestHandler):
    server_version = "CampoMock/0.1"

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self):
        h = self.headers.get("Authorization", "")
        m = re.match(r"Bearer\s+([\w-]+):([\w-]+)$", h)
        return bool(m) and m.group(1) == PROJECT and m.group(2) in CODES

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Content-Range")
        self.end_headers()

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/api/campo/config":
            return self._json(200, CONFIG)
        if p == "/api/transparency.json":
            return self._json(200, json.loads((ROOT / "fixtures" / "transparency.json").read_text(encoding="utf-8")))
        if p == "/api/campo/ledger.jsonl":
            return self._json(200, [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()])
        if p == "/api/campo/visits":
            vs = [json.loads(f.read_text(encoding="utf-8")) for f in VISITS.glob("*.json")]
            vs.sort(key=lambda v: v.get("received_at", ""), reverse=True)
            return self._json(200, vs)
        m = re.match(rf"^/api/campo/visits/({UUID})$", p)
        if m:
            v = load(m.group(1))
            return self._json(200, v) if v else self._json(404, {"ok": False, "error": "not-found"})
        if p == "/review":
            return self._html(self.review_page())
        if p == "/":
            return self._html("<p>NIDO Campo mock. See <a href='/review'>/review</a> and <a href='/api/campo/config'>/api/campo/config</a>.</p>")
        self._json(404, {"ok": False})

    def do_PUT(self):
        if not self._auth():
            return self._json(401, {"ok": False, "error": "bad-invite-code"})
        p = self.path.split("?")[0]
        m = re.match(rf"^/api/campo/visits/({UUID})$", p)
        if m:
            try:
                v = json.loads(self._body().decode("utf-8"))
            except Exception:
                return self._json(400, {"ok": False, "error": "bad-json"})
            if v.get("id") != m.group(1) or v.get("schema") != "campo/1":
                return self._json(400, {"ok": False, "error": "id-or-schema-mismatch"})
            old = load(v["id"])
            if old:  # keep server-side fields across retries
                for k in ("received_at", "review", "transcripts", "suggested"):
                    if k in old:
                        v[k] = old[k]
            v.setdefault("received_at", now())
            v.setdefault("review", {"status": "pending"})
            # reconcile media: keep what we already confirmed
            have = {x["id"]: x for x in (old or {}).get("media", []) if x.get("confirmed")}
            for mm in v.get("media", []):
                if mm["id"] in have:
                    mm["confirmed"] = True
                    mm["sha256"] = have[mm["id"]]["sha256"]
            save(v)
            return self._json(200, v)
        m = re.match(rf"^/api/campo/visits/({UUID})/media/([\w.-]+)$", p)
        if m:
            vid, mid = m.groups()
            v = load(vid)
            if not v:
                return self._json(404, {"ok": False, "error": "visit-first"})
            data = self._body()
            sha = hashlib.sha256(data).hexdigest()
            rec = next((x for x in v.get("media", []) if x["id"] == mid), None)
            if rec is None:
                rec = {"id": mid, "kind": "file"}
                v.setdefault("media", []).append(rec)
            (MEDIA / vid).mkdir(parents=True, exist_ok=True)
            ext = Path(rec.get("file", "")).suffix or ".bin"
            (MEDIA / vid / f"{mid}{ext}").write_bytes(data)
            rec.update({"sha256": sha, "bytes": len(data), "confirmed": True})
            save(v)
            return self._json(200, {"ok": True, "id": mid, "sha256": sha, "bytes": len(data)})
        self._json(404, {"ok": False})

    def do_POST(self):
        p = self.path.split("?")[0]
        m = re.match(rf"^/api/campo/visits/({UUID})/review$", p)
        if not m:
            return self._json(404, {"ok": False})
        v = load(m.group(1))
        if not v:
            return self._json(404, {"ok": False, "error": "not-found"})
        try:
            body = json.loads(self._body().decode("utf-8") or "{}")
        except Exception:
            body = {}
        action = body.get("action")
        minors = any(x.get("minors_present") for x in v.get("media", []))
        if action == "approve_public" and (minors or v.get("consent", {}).get("scope") != "publishable"):
            return self._json(409, {"ok": False, "error": "public-blocked", "reason": "minors_present" if minors else "consent-internal"})
        if action not in ("approve_internal", "approve_public", "reject"):
            return self._json(400, {"ok": False, "error": "bad-action"})
        v["review"] = {"status": action, "note": body.get("note", ""), "at": now(), "by": body.get("by", "organizer")}
        ev = append_event(event_for(v)) if action.startswith("approve") else None
        save(v)
        return self._json(200, {"ok": True, "review": v["review"], "event": ev})

    def review_page(self):
        vs = [json.loads(f.read_text(encoding="utf-8")) for f in VISITS.glob("*.json")]
        vs.sort(key=lambda v: v.get("received_at", ""), reverse=True)
        rows = []
        for v in vs:
            media = "".join(
                f"<li>{x.get('kind')} {x['id']} {'✔' if x.get('confirmed') else '…'} "
                f"{'· se reconoce a alguien' if x.get('people_identifiable') else ''}"
                f"{' · <b>hay niñas o niños</b>' if x.get('minors_present') else ''}</li>" for x in v.get("media", []))
            st = v.get("review", {}).get("status", "pending")
            rows.append(f"""<article style='border:1px solid #ccc;border-radius:8px;padding:12px;margin:12px 0'>
<b>{v.get('visit_type')}</b> · {v.get('vereda')} · {v.get('site_ref')} · {v.get('author')} · {v.get('started_at','')[:16]}
<span style='float:right'>{st}</span>
<pre style='white-space:pre-wrap;background:#f6f3ec;padding:8px'>{json.dumps(v.get('answers', {}), ensure_ascii=False, indent=1)}</pre>
<ul>{media}</ul>
<form method='post' action='/api/campo/visits/{v['id']}/review' onsubmit='return send(event, this)'>
<button name='action' value='approve_internal'>Aprobar interno</button>
<button name='action' value='approve_public'>Aprobar público</button>
<button name='action' value='reject'>Rechazar</button>
</form></article>""")
        return f"""<!doctype html><meta charset='utf-8'><title>Inbox · NIDO Campo mock</title>
<body style='font-family:system-ui;max-width:800px;margin:24px auto;padding:0 16px'>
<h1>Inbox (mock)</h1><p>{len(vs)} visitas. Las aprobaciones escriben en <code>mock-server/data/ledger.jsonl</code>.</p>
{''.join(rows) or '<p>Nada todavía. Sube una visita con <code>mock-server/post_fixture.sh</code>.</p>'}
<script>
async function send(e, f) {{ e.preventDefault(); const action = e.submitter.value;
 const r = await fetch(f.action, {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{action}})}});
 const j = await r.json(); alert(r.ok ? 'OK: ' + action : 'Bloqueado: ' + (j.reason || j.error)); location.reload(); return false; }}
</script>"""

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.command, self.path))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"NIDO Campo mock for project '{PROJECT}' on http://localhost:{port}  (inbox: /review)")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
