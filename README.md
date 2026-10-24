# NIDO Campo

Field-visit tools for the Pijao, Quindío rebuild (Alianza Nido), built at Hack for Humanity Portland, October 24, 2026. MIT licensed. Everything here belongs to the Pijao community.

**Read first:** `docs/builder-one-sheet.pdf` (2 pages). Depth: `docs/build-brief.pdf`. Hosts: `docs/host-guide.pdf`.

## Three tables

| Table | Folder | Build |
|---|---|---|
| The phone | `app/` | Android app that works with no signal: pick a visit type, answer Spanish questions, voice notes, photos with consent flags, uploads itself when online |
| The inbox | `server/` + `ai/` | Receives visits and files, review page (approve internal, approve public, reject), Gemini transcript and suggestions |
| The board | `dashboard/` | One public page reading `transparency.json`: money, houses, mingas |

Each table can demo alone against the mock server and the fixtures. Pick whatever stack you are fastest in.

## Quick start (2 minutes, no installs)

```bash
git clone <this repo> && cd nido-campo
python3 mock-server/server.py          # http://localhost:8080  (Python 3.8+, stdlib only)
# in another terminal:
mock-server/post_fixture.sh            # uploads two sample visits
open http://localhost:8080/review      # the inbox, with the approve buttons
```

Try it: click **Aprobar público** on the minga visit. It is blocked, because one photo is flagged "hay niñas o niños". Click **Aprobar interno**: a line is appended to `mock-server/data/ledger.jsonl`. That is the whole flow.

## What is where

```
config/nido-pijao/project-config.json    the seven visit types, their questions, veredas, sites, invite codes
config/demo-huerta-escolar/              a second, fake project: swap it in to prove the app is generic
fixtures/visit-minga.json, visit-obra.json   two complete visit records (campo/1)
fixtures/ledger.jsonl, transparency.json     the board's inputs, with today's real Nido numbers
fixtures/media/                          sample photos and voice notes (consented) once added
mock-server/server.py                    the contract, implemented in 200 lines; the inbox table replaces it
docs/                                    one-sheet, brief, host guide, the flow diagram
```

## The contract (campo/1)

The phone owns the visit `id` (UUID v4). Sending anything twice is safe.

| Call | Means |
|---|---|
| `GET /api/campo/config` | the project config (the app also ships with a bundled copy) |
| `PUT /api/campo/visits/{id}` | here is a visit (JSON, under 256 KB). Same id twice: 200, same answer |
| `PUT /api/campo/visits/{id}/media/{media_id}` | here is one file (raw bytes). Same sha256 twice: fine |
| `GET /api/campo/visits/{id}` | what do you have? The phone marks the visit `synced` when every file is confirmed |
| `POST /api/campo/visits/{id}/review` | `{"action": "approve_internal" \| "approve_public" \| "reject", "note": ""}` |
| header | `Authorization: Bearer nido-pijao:pijao-2026` (codes are in the config) |

Visit shape: see `fixtures/visit-minga.json`. `answers` is flat; its keys come from the config, so adding a question never changes the schema. Server-only fields (`received_at`, `review`, `transcripts`, `suggested`) are never sent by the phone.

Approve writes one event to the ledger (`transparency/1`), e.g.

```json
{"id":"evt_0007","at":"2026-10-03","type":"minga","site":"sendero-arenales","attendees":14,"meals":18,"meal_funder":"sancocho-club","source":"campo:6f1c…","by":"review"}
```

The board reads `transparency.json`, which a script rebuilds from those events (the mock serves the fixture at `/api/transparency.json`).

## Three rules, no exceptions

1. **No GPS, coordinates, addresses or ID numbers anywhere.** Location is a vereda picked from a list. Strip EXIF from photos before upload.
2. **Nothing goes public without a human clicking approve.** A photo flagged `minors_present` can never go public, whatever the consent says. Default consent scope is `internal`.
3. **Use the consented sample media in `fixtures/media/`.** No children in the demo.

## Recipes

**Phone table, no Android Studio?** Build a web app that installs from Chrome:
`npm create vite@latest app -- --template react` (or vanilla), add `vite-plugin-pwa` for offline, Dexie for the local queue, `MediaRecorder` for voice, `<input type="file" accept="image/*" capture="environment">` for photos, `browser-image-compression` to shrink and strip EXIF. Test on a real phone over https with `npx cloudflared tunnel --url http://localhost:5173` (or ngrok). On Chrome: menu, "Add to Home screen". If someone has Flutter ready, `flutter create app` and the same shape: `drift`/`sqflite`, `image_picker`, `record`, `connectivity_plus`, `dio`.

**Inbox table.** Copy `mock-server/server.py` into `server/` and grow it, or rewrite in Node/Go. For Gemini: a free key from Google AI Studio; send the m4a for a Spanish transcript, then ask for JSON matching the visit type's field keys (structured output), then captions and the two flags per photo. Write results into the visit under `transcripts` and `suggested`; the review page shows them highlighted. A `minors_present: true` guess can only lock public, never unlock it.

**Board table.** Plain HTML + one JS module reading `fixtures/transparency.json` is enough. Spanish first, EN toggle, must look right at 360 px. COP formats as `$14.855.460`, USD as `$1,982`. Every number should link to the events behind it.

## FAQ from Pijao (so you do not have to guess)

- **Who holds the phone?** Coordinators from AHO! and Espejo de Agua, La Semilla (a farm family), the maestro de obra, Saturday volunteers. Mid-range or older Androids. Gloves, sun, one hand free: big buttons, few screens.
- **Is there signal at the farms?** Mostly no. Wifi in town. Uploads must survive a dropped connection and retry.
- **Do we need accounts?** No. One invite code per territory. The device remembers the person's name.
- **Why no GPS, even internal?** Community leaders have asked not to be findable. The privacy page promises geography stops at the vereda. We keep that promise in code.
- **What does a minga visit need at minimum?** How many people came, what got done, how many plates of sancocho, a couple of photos, a voice note. That is the demo.
- **What is a vereda?** A rural district of a municipio, like a township. The veredas list in the config is a starting point; the field team will correct it.
- **Can we invent a field?** Add it to the config, not the code. The whole point is that the same app serves the next project.
- **What happens after today?** AHO! and Espejo de Agua take the repo to Pijao in November and test it on a real minga. You will hear how it went.

## Credits

Alianza Nido: Corporación Espejo de Agua, AHO! Wellness Tech, Esto es Quindío, NIDO | Hogares Vivos, La Semilla, Sancocho Club. Event: The AI Collective Portland, with Google and MLH. Questions: info@espejodeagua.org · espejodeagua.org/nido
