# Sample media (add before Saturday)

Put here, with the file names the fixtures expect:

- `6f1c2a4e-9b0d-4d3a-a6f2-0c5b8e7d1a22/01.jpg`, `02.jpg` and `a1.m4a` (minga visit)
- `b2d7e5a1-3c44-4f0e-9d21-5e6f7a8b9c01/01.jpg` and `a1.m4a` (obra visit)

Rules: only photos with recorded consent, no children, EXIF already stripped
(the website's `deploy/fotos.py` does that). `a1.m4a` = a 30 to 90 second
voice note in Colombian Spanish describing the visit. If a file is missing the
mock server still works; the inbox just shows "archivo pendiente".
