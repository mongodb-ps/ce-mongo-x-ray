#!/bin/bash
# Add or update the MongoDB copyright header on every Python file in this
# checkout: core's src/ and tests/, plus every local plugin checkout under
# plugins/ (their src/ and tests/). If a file already starts with the
# copyright docstring it is replaced with the current one; otherwise the
# current header is prepended. The year always reflects the current year.

YEAR="$(date +%Y)"

COPYRIGHT='"""
Copyright (c) '"$YEAR"' MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""'

find src tests plugins/*/src plugins/*/tests -type f -name "*.py" 2>/dev/null | sort | while read -r file; do
    python3 - "$file" "$COPYRIGHT" <<'PYEOF'
import re
import sys

path, block = sys.argv[1], sys.argv[2]

FUTURE_RE = re.compile(r"^(?:from __future__ import[^\n]*\n)+", re.M)
DISCLAIMER_END = 'THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.'


def extract_docstring(text: str) -> tuple[str, str]:
    """Return the leading ``\"\"\"...\"\"\"`` docstring (if any) and the rest."""
    text = text.lstrip("\n")
    if text.startswith('"""'):
        end = text.find('"""', 3)
        if end != -1:
            return text[: end + 3], text[end + 3 :]
    return "", text


def doc_description(doc: str) -> str:
    """Module-description part of a leading docstring.

    For a copyright header this is the text after the disclaimer; for a plain
    module docstring it is the whole content. Empty for a bare header.
    """
    if not doc:
        return ""
    inner = doc[3:-3]
    if "Copyright (c)" in inner:
        idx = inner.find(DISCLAIMER_END)
        if idx == -1:
            return ""
        return inner[idx + len(DISCLAIMER_END) :].strip("\n").strip()
    return inner.strip()


with open(path, encoding="utf-8") as fh:
    text = fh.read()
orig = text

# Leading docstring (copyright header and/or module docstring).
doc1, body = extract_docstring(text)
# Keep any from __future__ imports directly after the header.
future = ""
if FUTURE_RE.search(body):
    match = FUTURE_RE.search(body)
    future = match.group(0).rstrip("\n")
    body = body[: match.start()] + body[match.end() :]
# A module docstring may follow the future imports (or the leading docstring).
doc2, rest = extract_docstring(body)

# Build the header docstring with any module description merged inside it.
inner = block[3:-3].strip("\n")
for part in (doc_description(doc1), doc_description(doc2)):
    if part:
        inner += "\n\n" + part
header = '"""\n' + inner + '\n"""'

new_text = header + "\n\n" + future + ("\n\n" if future else "") + rest.lstrip("\n")
if new_text != orig:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    print(f"Updated: {path}")
else:
    print(f"Skipping (already current): {path}")
PYEOF
done

echo "All done!"
