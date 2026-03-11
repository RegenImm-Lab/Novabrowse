#!/bin/sh -

cd /data || exit

# With Docker, we need to set up a separate application user ("appuser")
# with the same UID and GID as the host user.  We don't need to do this
# with Apptainer, because it will automatically map the host user to the
# same UID and GID inside the container.
host_uid=$(stat -c '%u' .)
host_gid=$(stat -c '%g' .)

if [ "$host_uid" != "$(id -u)" ] || [ "$host_gid" != "$(id -g)" ]
then
        # If the host UID or GID are different from the current user,
        # we need to create a new user with the same UID and GID as the
        # host user.

	doas groupadd -o -g "$host_gid" appuser
	doas useradd -o -u "$host_uid" -g "$host_gid" appuser

	switch_users=true

fi

case $1 in
	*.ipynb)
                # If the first argument is a Jupyter notebook, run the
                # convert-and-run script as the appuser. This script
                # will convert the notebook to a Python script and then
                # execute it.
		if "${switch_users-false}"; then
			doas -u appuser /app/convert-and-run.sh "$@"
		else
			/app/convert-and-run.sh "$@"
		fi
		;;
	*)
                # If the first argument is not a Jupyter notebook, just
                # execute it. This allows the container to run any
                # command, not just Jupyter notebooks.
		exec "$@"
esac
