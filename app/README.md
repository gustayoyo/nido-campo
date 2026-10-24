# The phone (app/)

Goal: a visit created with airplane mode on (type, a few answers, a voice note, two photos with consent flags) that uploads itself when wifi is back and shows `synced`.

Start here: `config/nido-pijao/project-config.json` is your screen definition. `visit_types[]` gives the triage buttons; each type's `fields[]` gives the questions; `header[]` is the same for every visit. Field `type` values: text, longtext, number, enum, multi, date, datetime, counts, matrix, items, photo, site, consent, followup. Render those and you are done; never write a screen per visit type.

Minimum for 3:30: types `minga` and `nota`, the header, voice + photo capture with the two flags, local save, sync to `PUT /api/campo/visits/{id}` then `PUT .../media/{id}`. Test against `python3 mock-server/server.py`.

No Android Studio: web app that installs from Chrome (recipe in the root README). Flutter ready: `flutter create app`.
