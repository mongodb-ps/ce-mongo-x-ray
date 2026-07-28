#!/bin/bash

roots=("$@")
if [ ${#roots[@]} -eq 0 ]; then
  roots=(".")
fi

# Process all .raw.html files in the requested directories recursively
find "${roots[@]}" -name "*.raw.html" -type f | while read -r file; do
  # Extract the directory and base name
  dir=$(dirname "$file")
  basename=$(basename "$file" .raw.html)
  
  # Create output filename by removing .raw
  output="$dir/${basename}.html"
  
  if [ -f "$output" ] && git diff --quiet "$file" && git diff --quiet "$output"; then
    echo "No changes in $file, skipping minification."
    continue
  fi
  echo "Minifying $file -> $output"
  npx html-minifier-terser "$file" -o "$output" \
    --collapse-whitespace --remove-comments --minify-js true --minify-css true
done

# Process all .raw.js files in the requested directories recursively
find "${roots[@]}" -name "*.raw.js" -type f | while read -r file; do
  # Extract the directory and base name
  dir=$(dirname "$file")
  basename=$(basename "$file" .raw.js)
  
  # Create output filename by removing .raw
  output="$dir/${basename}.js"
  
  if [ -f "$output" ] && git diff --quiet "$file" && git diff --quiet "$output"; then
    echo "No changes in $file, skipping minification."
    continue
  fi
  echo "Minifying $file -> $output"
  npx terser "$file" -o "$output" -c -m
done

# Process all .raw.css files in the requested directories recursively
find "${roots[@]}" -name "*.raw.css" -type f | while read -r file; do
  dir=$(dirname "$file")
  basename=$(basename "$file" .raw.css)
  output="$dir/${basename}.css"

  if [ -f "$output" ] && git diff --quiet "$file" && git diff --quiet "$output"; then
    echo "No changes in $file, skipping minification."
    continue
  fi
  echo "Minifying $file -> $output"
  python3 -c "
import re, sys

with open(sys.argv[1]) as f:
    css = f.read()

# Remove comments
css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
# Remove whitespace around {};:,
css = re.sub(r'\s*([{};:,])\s*', r'\1', css)
# Replace multiple whitespace with single space
css = re.sub(r'\s+', ' ', css)
# Remove whitespace before and after () as much as possible
css = re.sub(r'\(\s+', '(', css)
css = re.sub(r'\s+\)', ')', css)
# Remove leading/trailing whitespace per block
css = re.sub(r';\s+}', '}', css)
css = css.strip()

with open(sys.argv[2], 'w') as f:
    f.write(css)
" "$file" "$output"
done
