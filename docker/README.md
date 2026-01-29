# Novabrowse in Docker

This directory contains the necessary files to run Novabrowse Jupyter
notebooks in a Docker container.

The benefit of using Docker is that it encapsulates all dependencies and
configurations, making it easier to set up and run the notebooks
consistently across different environments.

## Prerequisites

- Basic knowledge of using the command line.
- Docker and Docker Compose installed on your machine.

## Setup

This Docker setup assumes that you have cloned the Novabrowse Git
repository.

It will make the directories `1_subject_sequences`, `2_subject_blastdb`,
`3_query_sequences`, and `4_blast_results` from the Git repository's
top-level directory available inside the Docker container (read/write).
It also makes the `chromosome_data.json` file available inside the
container (read-only), including any modifications you may have made to
it.

Make a copy of the `novabrowse.env.example` file and name it
`novabrowse.env` in the `docker` directory. Edit the `novabrowse.env`
file to set any environment variables as needed. Currently, the only
required environment variable is `ENTREZ_EMAIL_ENV`, which should be set
to your email address for NCBI Entrez access, but also see the note
about caching below.

## Basic Usage

To run, e.g., the `novabrowse_1.0.ipynb` notebook, use

``` shell
./run_notebook ../novabrowse_1.0.ipynb
```

or

``` shell
./docker/run_notebook novabrowse_1.0.ipynb
```

... depending on what your current working directory is.

This command will build the Docker image (if not already built), which
includes converting the given notebook to a Python script, and then run
the generated script inside a Docker container.

The generated output files will be available in the `novabrowse_output`
directory in the same directory as the `run_notebook` script (the exact
path will be printed to the terminal when the run completes). If this
directory does not exist, it will be created.

## A note about caching

To speed up repeated runs, the Docker setup caches downloaded NCBI data
in a persistent Docker volume named `novabrowse_ncbi_cache`. This cache
is used to store data downloaded from NCBI, so that subsequent runs do
not need to re-download the same data. All calls to the `Entrez.efetch`
and `Entrez.esearch` functions from the Biopython library will use this
cache.

The size of the cache is limited to 500 MB, or to the value of the
`ENTREZ_CACHE_SIZE_MB` variable in the `novabrowse.env` file, if set.
You may want to increase this limit if you are working with a large
number of sequences, or if a single request is likely to exceed 500 MB
(e.g., downloading large genomes). A single run of the default
`novabrowse_1.0.ipynb` notebook uses about 75 MB of cache space.

Setting the `ENTREZ_USE_CACHE` variable in the `novabrowse.env` file to
`false` will disable the use of the cache entirely. Doing so will not
clear the existing cache, but will cause all NCBI data to be
re-downloaded on each request for the duration of the run.

The cache volume can be removed using the command

``` shell
docker volume rm novabrowse_ncbi_cache
```
