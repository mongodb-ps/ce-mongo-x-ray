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
import sys

path, block = sys.argv[1], sys.argv[2]

with open(path, encoding="utf-8") as fh:
    text = fh.read()
orig = text

# If the file starts with a docstring that contains the copyright notice,
# replace that whole docstring with the current header.
if text.startswith('"""'):
    end = text.find('"""', 3)
    if end != -1 and "Copyright (c)" in text[:end]:
        rest = text[end + 3 :].lstrip("\n")
        new_text = block.rstrip("\n") + "\n\n" + rest
        if new_text != orig:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new_text)
            print(f"Updated: {path}")
        else:
            print(f"Skipping (already current): {path}")
        sys.exit(0)

# No copyright header: prepend it.
new_text = block.rstrip("\n") + "\n\n" + text.lstrip("\n")
if new_text != orig:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    print(f"Added: {path}")
else:
    print(f"Skipping (already current): {path}")
PYEOF
done

echo "All done!"
