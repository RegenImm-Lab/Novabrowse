#!/bin/sh -

cd /data || exit

# Pick up the UID and GID of the host user from the current directory
# (/data) and create a user with the same UID and GID inside the
# container. This allows the container to read and write files in the
# mounted volume without permission issues.
HOST_UID=$(stat -c '%u' .)
HOST_GID=$(stat -c '%g' .)

doas groupadd -o -g "$HOST_GID" appuser
doas useradd -o -u "$HOST_UID" -g "$HOST_GID" appuser

case $1 in
	*.ipynb)
                # If the first argument is a Jupyter notebook, run the
                # convert-and-run script as the appuser. This script
                # will convert the notebook to a Python script and then
                # execute it.
		doas -u appuser "$HOME/convert-and-run.sh" "$@"
		;;
	*)
                # If the first argument is not a Jupyter notebook, just
                # execute it as the appuser. This allows the container
                # to run any command, not just Jupyter notebooks.
		exec "$@"
esac
