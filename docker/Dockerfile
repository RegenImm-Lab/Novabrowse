# Dockerfile for setting up a docker-ised environment to run Novabrowse.

# --- Base stage with system packages and user setup.
#FROM python:slim AS base
FROM debian:stable-slim

ARG UID=1000
ARG GID=1000

# Install required system packages.
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache \
    --mount=type=cache,target=/var/lib/apt/lists,id=apt-lists-cache \
	apt-get update && \
	DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
		curl \
		doas \
		dos2unix \
		python3-biopython \
		python3-diskcache \
		python3-ipython \
		python3-jupyterlab-pygments \
		python3-libsass \
		python3-nbconvert \
		python3-yaml

# Set up our non-root user.
ENV HOME="/app"

RUN groupadd -g "$GID" novabrowse && \
    useradd -m -u "$UID" -g "$GID" -d "$HOME" novabrowse && \
    chmod a+rx "$HOME"

# Allow the user "novabrowse" to use "doas" without a password, which is
# necessary for some operations in the entrypoint script.
RUN echo 'permit nopass novabrowse' >/etc/doas.conf && chmod 440 /etc/doas.conf

# Drop root privileges.
USER "$UID:$GID"

WORKDIR "$HOME"

# Pixi isn't available via system packages, so install it manually.
RUN curl -fsSL https://pixi.sh/install.sh | sh -s
ENV PATH="$HOME/.pixi/bin:$PATH"

# Install BLAST using Pixi.
RUN --mount=type=cache,id=pixi-cache,uid="$UID",gid="$GID",target="$HOME/.cache/pixi" \
    --mount=type=cache,id=rattler-cache,uid="$UID",gid="$GID",target="$HOME/.cache/rattler" \
	pixi config set default-channels '["conda-forge", "bioconda"]' && \
	pixi global install blast

COPY --chown="$UID:$GID" ncbi_cache.py ncbi_cache.py
COPY --chown="$UID:$GID" --chmod=755 entrypoint.sh entrypoint.sh
COPY --chown="$UID:$GID" --chmod=755 convert-and-run.sh convert-and-run.sh
RUN dos2unix entrypoint.sh convert-and-run.sh

ENTRYPOINT ["/app/entrypoint.sh"]
