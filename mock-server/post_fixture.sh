#!/usr/bin/env bash
# Posts the fixture visits to the mock (or to the inbox table's server). Usage:
#   mock-server/post_fixture.sh                 # -> http://localhost:8080
#   mock-server/post_fixture.sh http://10.0.0.5:8080
set -e
URL="${1:-http://localhost:8080}"
AUTH="Authorization: Bearer nido-pijao:pijao-2026"
for f in fixtures/visit-minga.json fixtures/visit-obra.json; do
  id=$(python3 -c "import json,sys; print(json.load(open('$f'))['id'])")
  echo "PUT $f -> $URL/api/campo/visits/$id"
  curl -sS -X PUT -H "$AUTH" -H "Content-Type: application/json" --data-binary @"$f" "$URL/api/campo/visits/$id" | head -c 200; echo
  # upload any sample media that exists for this visit
  for m in fixtures/media/$id/*; do
    [ -f "$m" ] || continue
    mid=$(basename "$m"); mid="${mid%.*}"; mid=$(echo "$mid" | sed 's/^0*\([0-9]\)/m\1/')
    echo "PUT media $m as $mid"
    curl -sS -X PUT -H "$AUTH" --data-binary @"$m" "$URL/api/campo/visits/$id/media/$mid" | head -c 200; echo
  done
done
echo "Open $URL/review"
