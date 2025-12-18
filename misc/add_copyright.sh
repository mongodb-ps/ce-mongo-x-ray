#!/bin/bash

COPYRIGHT="\"\"\"
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES. 
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION. 
THIS MATERIAL IS PROVIDED \"AS IS\" WITHOUT WARRANTY OR LIABILITY.
\"\"\""

find src tests -type f -name "*.py" 2>/dev/null | while read -r file; do
    if ! grep -q "Copyright" "$file"; then
        echo "Processing: $file"
        
        { printf "%s\n" "$COPYRIGHT"; cat "$file"; } > "$file.tmp"
        
        mv "$file.tmp" "$file"
    else
        echo "Skipping (copyright already exists): $file"
    fi
done

echo "All done!"