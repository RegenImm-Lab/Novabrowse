# Novabrowse in Docker

This directory contains the necessary files to build a Docker container
that is able to run the Novabrowse Jupyter notebooks
(`make_blastdb.ipynb`, `get_chromosome_info.ipynb`, and
`novabrowse_1.0.ipynb`)

The benefit of using Docker is that it encapsulates all dependencies,
making it easier to set up and run the notebook consistently across
different environments.

## Prerequisites

- Basic knowledge of using the command line.
- Docker installed on your machine (with the Docker service up and
  running), if you want to build and/or run the container locally.
- Apptainer installed on your machine, if you want to run the pre-built
  Docker image using Apptainer instead of Docker.
- This repository cloned from GitHub.

## Setup

This Docker setup assumes that you have cloned the Novabrowse Git
repository.

Fill out the value for the `entrez_email:` section at the top of the
`novabrowse_config.yaml` file. The value should be the email address
that you will use when making requests to NCBI. The rest of the
configuration file mirrors the default configuration found in the
various notebooks, but overrides these.

If the YAML configuration file is not found, the notebooks will fall
back to using the default configuration values from the notebooks
themselves.

## Basic Usage

### Building the Docker container locally

To build the Docker container locally, run the following command from
the `docker` subdirectory of this Git repository:

``` shell
docker build -t novabrowse:latest .
```

### Pulling the Docker image from a Docker registry

Instead of building the Docker container locally, you can pull a
pre-built image from a Docker registry, such as GitHub Container
Registry:

``` shell
docker pull ghcr.io/regenimm-lab/novabrowse:latest
```

Please have a look at the GitHub Container Registry page for this
repository for the latest available image tags:
https://github.com/RegenImm-Lab/Novabrowse/pkgs/container/novabrowse

### Running the Docker container

To run the Docker container, you would use the following command from
the Git repository's top-level directory:

``` shell
docker run -t -v "$PWD:/data" novabrowse {notebook_filename}
```

... where `{notebook_filename}` is the name of the notebook you want to
run, such as `novabrowse_1.0.ipynb`.

### Running the Docker container with Apptainer

If you are using Apptainer instead of Docker, you can run the container
by converting the Docker image to an Apptainer SIF file and then running
it.

First, convert the Docker image to an SIF file:

``` shell
apptainer pull novabrowse.sif ghcr.io/regenimm-lab/novabrowse:latest
```

Then, run the Apptainer container:

``` shell
apptainer run -e --bind "$PWD:/data" novabrowse.sif {notebook_filename}
```

## A note about caching

To speed up repeated runs, the code in the container caches downloaded
NCBI data in the directory `tmp/ncbi_cache` in the current directory.
This cache is used to store data downloaded from NCBI, so that
subsequent runs do not need to re-download the same data. All calls to
the `Entrez.efetch` and `Entrez.esearch` functions from the Biopython
library will use this cache.

The size of the cache is limited to 500 MB, or to the value of the
`ENTREZ_CACHE_SIZE_MB` environment variable, if set. You may want to
increase this limit if you are working with a large number of sequences,
or with large individual requests (e.g., downloading large genomes). A
single run of the default `novabrowse_1.0.ipynb` notebook uses about 75
MB of cache space.

Setting the `ENTREZ_USE_CACHE` environment variable to `false` will
disable the use of the cache entirely. Doing so will not clear the
existing cache, but will cause all NCBI data to be re-downloaded on each
request for the duration of the run.

Environment variables can be set when running the Docker container by
adding `-e {ENV_VAR_NAME}={VALUE}` to the `docker run` command.

The cache can be removed by simply deleting the `tmp/ncbi_cache`
directory:

``` shell
rm -rf tmp/ncbi_cache
```
