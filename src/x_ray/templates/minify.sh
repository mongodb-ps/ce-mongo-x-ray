#!/bin/bash

# Process all .raw.html files in all subdirectories recursively
find . -name "*.raw.html" -type f | while read -r file; do
  # Extract the directory and base name
  dir=$(dirname "$file")
  basename=$(basename "$file" .raw.html)
  
  # Create output filename by removing .raw
  output="$dir/${basename}.html"
  
  if git diff --quiet "$file" && git diff --quiet "$output"; then
    echo "No changes in $file, skipping minification."
    continue
  fi
  echo "Minifying $file -> $output"
  npx html-minifier-terser "$file" -o "$output" \
    --collapse-whitespace --remove-comments --minify-js true --minify-css true
done

# Process all .raw.js files in all subdirectories recursively
find . -name "*.raw.js" -type f | while read -r file; do
  # Extract the directory and base name
  dir=$(dirname "$file")
  basename=$(basename "$file" .raw.js)
  
  # Create output filename by removing .raw
  output="$dir/${basename}.js"
  
  if git diff --quiet "$file" && git diff --quiet "$output"; then
    echo "No changes in $file, skipping minification."
    continue
  fi
  echo "Minifying $file -> $output"
  npx terser "$file" -o "$output" -c -m
done