# The inbox (server/ + ai/)

Goal: a visit from the phone (or `mock-server/post_fixture.sh`) is listed, its audio plays, the Gemini transcript shows, and "Aprobar público" is blocked while a photo is flagged "hay niñas o niños". Approve writes a ledger event.

Start here: `mock-server/server.py` already implements the contract and a bare review page. Copy it here and make the review page good (play audio, show photos with their flags, show `transcripts` and `suggested`, three buttons), or rewrite it in your stack keeping the same routes.

Gemini (free key from Google AI Studio): on each media upload, transcribe audio; with the visit type's field keys, ask for JSON `suggested` answers (only for empty fields); for photos, captions ES/EN plus `people_identifiable` and `minors_present`. Store under the visit; never auto-publish.
