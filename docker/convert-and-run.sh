#!/bin/sh -

PATH=/app/.pixi/bin:/app/.venv/bin:$PATH

TMPDIR=$PWD/tmp

notebook=$1
scriptname=$(basename "$notebook" .ipynb).py

if [ ! -f "$notebook" ]; then
	printf 'Error: notebook file "%s" does not exist.\n' "$notebook" >&2
	exit 1
fi

if ! mkdir -p "$TMPDIR/ncbi_cache"; then
	echo 'Could not create required temporary directories.' >&2
	exit 1
fi

if ! python3 -m nbconvert --to script "$notebook" --output-dir="$TMPDIR"
then
	printf 'Error: could not convert notebook "%s" to Python script.\n' "$notebook" >&2
	exit 1
fi

monkey_patch=docker/ncbi_cache.py
if [ -f "$monkey_patch" ]; then
	tmpfile=$(mktemp)

	cat "$monkey_patch" "$TMPDIR/$scriptname" >"$tmpfile" &&
	mv -f "$tmpfile" "$TMPDIR/$scriptname"
fi

exec python3 "$TMPDIR/$scriptname"
