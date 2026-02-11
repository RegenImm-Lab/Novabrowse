#!/bin/sh -

set -u

# Get the UID and GID from the /project/novabrowse_output directory
OUTPUT_DIR=novabrowse_output

USER_ID=1000
GROUP_ID=1000

if [ -d "$OUTPUT_DIR" ]; then
    USER_ID=$(stat -c "%u" "$OUTPUT_DIR")
    GROUP_ID=$(stat -c "%g" "$OUTPUT_DIR")
else
    printf 'Directory "%s" does not exist. Using default UID and GID.\n' "$OUTPUT_DIR" >&2
fi
printf 'Using UID: %s and GID: %s\n' "$USER_ID" "$GROUP_ID" >&2

# Change ownership of the NCBI cache directory to the determined UID and
# GID.
chown -R "$USER_ID:$GROUP_ID" ncbi_cache/

gosu "$USER_ID:$GROUP_ID" python3 notebook.py >&2

# Copy created output files to the output directory.
mv Novabrowse_*.html gene_fetch.log "$OUTPUT_DIR"/
