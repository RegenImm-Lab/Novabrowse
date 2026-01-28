# Novabrowse in Docker

This directory contains the necessary files to run Novabrowse Jupyter
notebooks in a Docker container.

The benefit of using Docker is that it encapsulates all dependencies and
configurations, making it easier to set up and run the notebooks
consistently across different environments.

## Prerequisites

- Basic knowledge of using the command line.
- Docker an Docker Compose installed on your machine.

## Setup

This Docker setup assumes that you have cloned the Novabrowse Git
repository.

It will make the directories `1_subject_sequences`, `2_subject_blastdb`,
`3_query_sequences`, and `4_blast_results` available inside the Docker
container (read/write). It also makes the `chromosome_data.json` file
available inside the container (read-only), including any modifications
you may have made to it.

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

The data is cached for three days. After this period, the cached data
will be considered stale and will be re-downloaded on the next request.
It's possible to modify the cache retention period by setting the
`ENTREZ_CACHE_EXPIRY_DAYS` variable in the `novabrowse.env` file to a
different number of days.

The cache volume can be removed using the command

``` shell
docker volume rm novabrowse_ncbi_cache
```
