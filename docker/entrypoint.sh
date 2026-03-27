#!/bin/sh -

cd /data || exit

# With Docker, we may need to set up a separate application user
# ("appuser") with the same UID and GID as the host user.  We don't need
# to do this with Apptainer, because it will automatically map the host
# user to the same UID and GID inside the container.  We use the UID and
# GID of the current directory (which is bind-mounted from the host) to
# determine the host UID and GID.
host_uid=$(stat -c '%u' .)
host_gid=$(stat -c '%g' .)

if [ "$host_uid" != "$(id -u)" ]; then
	# If the host UID is different from the current user, we need to
	# create a new user with the same UID and GID as the host user.
	# Note: A difference in only GID is considered acceptable.

	doas groupadd -o -g "$host_gid" appuser
	doas useradd -o -u "$host_uid" -g "$host_gid" appuser

	switch_users=true

fi

export NOVABROWSE_CONFIG="${NOVABROWSE_CONFIG:-./novabrowse_config.yaml}"

case $1 in
	*.ipynb)
		# If the first argument is a Jupyter notebook, run the
		# convert-and-run script as the appuser. This script
		# will convert the notebook to a Python script and then
		# execute it.
		if "${switch_users-false}"; then
			doas -u appuser \
				env NOVABROWSE_CONFIG="$NOVABROWSE_CONFIG" \
				ENTREZ_EMAIL_ENV="${ENTREZ_EMAIL_ENV-}" \
				/app/convert-and-run.sh "$@"
		else
			/app/convert-and-run.sh "$@"
		fi
		;;
	*)
		# If the first argument is not a Jupyter notebook, just
		# execute it. This allows the container to run any
		# command, not just Jupyter notebooks.
		if "${switch_users-false}"; then
			exec doas -u appuser "$@"
		else
			exec "$@"
		fi
esac
