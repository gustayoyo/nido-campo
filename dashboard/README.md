# The board (dashboard/)

Goal: one page that renders `fixtures/transparency.json` (real Nido numbers): money raised vs goal, each house with its step bar and budget, mingas and meals. Spanish first, EN toggle, right at 360 px. Every number links to the events behind it (`ledger.jsonl`).

Start: `index.html` + one JS module, `fetch('../fixtures/transparency.json')` (or `/api/transparency.json` from the mock). No names of people anywhere. COP as `$14.855.460`, USD as `$1,982`.
