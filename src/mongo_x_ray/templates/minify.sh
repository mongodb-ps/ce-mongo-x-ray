#!/bin/bash
set -euo pipefail

_git_root=$(git rev-parse --show-toplevel)

# Get changed raw files relative to templates dir
changed=$(git -C "$_git_root" diff --name-only -- src/mongo_x_ray/templates/ \
  | grep -E '\.raw\.(html|js|css)$' \
  | sed 's|^src/mongo_x_ray/templates/||' \
  || true)

if [ -z "$changed" ]; then
  echo "No changed .raw.* files to minify."
  exit 0
fi

while IFS= read -r file; do
  dir=$(dirname "$file")
  basename_raw=$(basename "$file")

  if [[ "$basename_raw" == *.raw.html ]]; then
    basename="${basename_raw%.raw.html}.html"
    echo "Minifying $file -> $dir/$basename"
    npx html-minifier-terser "$file" -o "$dir/$basename" \
      --collapse-whitespace --remove-comments --minify-js true --minify-css true
  elif [[ "$basename_raw" == *.raw.js ]]; then
    basename="${basename_raw%.raw.js}.js"
    echo "Minifying $file -> $dir/$basename"
    npx terser "$file" -o "$dir/$basename" -c -m
  elif [[ "$basename_raw" == *.raw.css ]]; then
    basename="${basename_raw%.raw.css}.css"
    echo "Minifying $file -> $dir/$basename"
    python3 -c "
import re, sys

with open(sys.argv[1]) as f:
    css = f.read()

css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
css = re.sub(r'\s*([{};:,])\s*', r'\1', css)
css = re.sub(r'\s+', ' ', css)
css = re.sub(r'\(\s+', '(', css)
css = re.sub(r'\s+\)', ')', css)
css = re.sub(r';\s+}', '}', css)
css = css.strip()

with open(sys.argv[2], 'w') as f:
    f.write(css)
" "$file" "$dir/$basename"
  fi
done <<< "$changed"
