#!/bin/sh -

# This script serves as the entrypoint for the Novabrowse Docker
# container.  It runs the Novabrowse notebook script and moves the
# generated HTML files to the appropriate directory.

if [ ! -f chromosome_data.json ]; then
	printf 'chromosome_data.json not found.\n' >&2
	exit 1
fi

echo 'Running Novabrowse notebook...' 2>&1
python3 notebook.py && mv Novabrowse*.html novabrowse_output/
