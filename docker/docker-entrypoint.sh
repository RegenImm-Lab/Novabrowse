#!/bin/sh -

set -u

# This script serves as the entrypoint for the Novabrowse Docker
# container.  It runs the Novabrowse script and moves the generated HTML
# files to the appropriate directory.

# OUTPUT_DIR is set in docker-compose.yml
# NOTEBOOK is set in Dockerfile

if [ ! -f chromosome_data.json ]; then
	printf 'chromosome_data.json not found.\n' >&2
	exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
	printf 'Output directory %s does not exist.\n' "$OUTPUT_DIR" >&2
	exit 1
fi

printf 'Running Novabrowse via "%s"...\n' "$NOTEBOOK.py" >&2
python3 "$NOTEBOOK.py" && mv Novabrowse*.html "$OUTPUT_DIR/"
