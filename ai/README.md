# ai/

Gemini helpers for the inbox table. Suggested shape:

- `transcribe.py <audio>` -> text
- `extract.py <transcript> <visit_type>` -> JSON with the type's field keys (structured output), confidence per field
- `caption.py <photo>` -> {alt_es, alt_en, people_identifiable, minors_present, faces_count}

Prompts as files in `ai/prompts/`, with the vereda and crop vocabulary from the config so names come out right. Free tier, Flash model. Skip cleanly if the key is missing.
