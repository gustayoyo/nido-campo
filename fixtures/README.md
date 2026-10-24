# fixtures/

- `visit-minga.json`, `visit-obra.json`: complete `campo/1` visit records. Post them with `mock-server/post_fixture.sh`.
- `ledger.jsonl`: `transparency/1` events, imported from the live site's `datos.json` as of Oct 3, 2026 plus the two fixture visits.
- `transparency.json`: the snapshot the board reads, consistent with the ledger.
- `media/`: sample consented photos and voice notes (see `media/README.md`).
