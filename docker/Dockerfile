# Dockerfile for setting up a docker-ised environment to run Novabrowse.
# It consists of three stages:
#
# 1. base:
#       Sets up the base Debian image with required system packages and
#       user/group configuration.
#
# 2. convert:
#       A intermediate stage that installs Jupyter nbconvert in a
#       virtual environment and converts the provided notebook to a
#       Python script.
#
# 3. runtime:
#       Installs BLAST using Pixi and sets up the Docker entrypoint to
#       run the converted script.

# --- Base stage with system packages and user setup.
#FROM python:slim AS base
FROM debian:stable-slim AS base

# Build arguments: UID and GID should match the host user to avoid
# permission issues.
ARG UID=1000
ARG GID=1000

ENV HOME="/project"

# The project directory will be writable by all.
RUN install -d -o "$UID" -g "$GID" -m 777 "$HOME"

ARG DEBIAN_FRONTEND=noninteractive

# Install required system packages.
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache \
    --mount=type=cache,target=/var/lib/apt/lists,id=apt-lists-cache \
	apt-get update && \
	apt-get install -y --no-install-recommends \
		curl \
		dos2unix \
		gosu \
		python3-biopython \
		python3-diskcache \
		python3-libsass \
		python3-venv \
		python3-yaml

# Drop root privileges.
USER "$UID:$GID"

WORKDIR "$HOME"

# --- Intermediate stage to convert notebook to script.
FROM base AS convert

RUN python3 -m venv --system-site-packages "$HOME/.venv"
ENV PATH="$HOME/.venv/bin:$PATH"

RUN --mount=type=cache,id=pip-cache,uid="$UID",gid="$GID",target="$HOME/.cache/pip" \
	pip install \
		jupyterlab_pygments \
		nbconvert

ARG NOTEBOOK

RUN --mount=type=bind,source="$NOTEBOOK",target=notebook.ipynb \
	jupyter-nbconvert --to script \
		notebook.ipynb \
		--output-dir "$HOME"

# Add caching header stub to generated notebook script.
RUN --mount=type=bind,source=docker/ncbi_cache-head.py,target=ncbi_cache-head.py \
	cat ncbi_cache-head.py notebook.py >notebook_tmp.py && \
	mv notebook_tmp.py notebook.py

# --- Final runtime stage to install BLAST and set up Docker entrypoint.
FROM base AS runtime

# Mount point for persistent NCBI cache.
RUN mkdir ncbi_cache

# Pixi isn't available via system packages, so install it manually.
RUN curl -fsSL https://pixi.sh/install.sh | sh -s
ENV PATH="$HOME/.pixi/bin:$PATH"

# Install BLAST using Pixi.
RUN --mount=type=cache,id=pixi-cache,uid="$UID",gid="$GID",target="$HOME/.cache/pixi" \
    --mount=type=cache,id=rattler-cache,uid="$UID",gid="$GID",target="$HOME/.cache/rattler" \
	pixi config set default-channels '["conda-forge", "bioconda"]' && \
	pixi global install blast

COPY --chown="$UID:$GID" docker/docker-entrypoint.sh docker-entrypoint.sh
RUN dos2unix docker-entrypoint.sh

# Copy the converted notebook script from the "convert" stage.
COPY --chown="$UID:$GID" docker/ncbi_cache.py ncbi_cache.py
COPY --chown="$UID:$GID" --from=convert "$HOME/notebook.py" notebook.py

USER root
CMD ["./docker-entrypoint.sh"]
