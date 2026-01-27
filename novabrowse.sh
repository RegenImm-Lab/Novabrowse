#!/bin/sh -

# This convenience script runs docker compose commands with the current
# user's UID and GID to avoid permission issues with created files.
# With no arguments, it defaults to running the container's default
# command.
#
# Usage:
#	./novabrowse.sh [docker compose command]
#
# Example (runs the Novabrowse container):
# 	./novabrowse.sh
#
# Example (clears the NCBI cache by removing the persistent volume):
#	./novabrowse.sh down -v
#

if [ "$#" = 0 ]; then
	set -- run --rm novabrowse
fi

exec env UID="$(id -u)" GID="$(id -g)" \
	docker compose --project-directory docker "$@"
