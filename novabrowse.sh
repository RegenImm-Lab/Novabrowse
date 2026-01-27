#!/bin/sh -

# This convenience script runs docker compose commands with the current
# user's UID and GID to avoid permission issues with created files.
# With no arguments, it defaults to running the container's default
# command.
#
# Usage:
#	./novabrowse.sh {docker compose command}
#
# Example:
#	./novabrowse.sh up --build
#

if [ "$#" = 0 ]; then
	set -- run --rm novabrowse
fi

exec env UID="$(id -u)" GID="$(id -g)" \
	docker compose "$@"
