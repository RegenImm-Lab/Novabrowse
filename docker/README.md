# Novabrowse in Docker

This directory contains the necessary files to run the Novabrowse
Jupyter notebook (`novabrowse_1.0.ipynb`) in a Docker container.

The benefit of using Docker is that it encapsulates all dependencies and
configurations, making it easier to set up and run the notebook
consistently across different environments.

## Prerequisites

- Basic knowledge of using the command line.
- Docker and Docker Compose installed on your machine (with the Docker
  service up and running).
- This repository cloned from GitHub.

## Setup

This Docker setup assumes that you have cloned the Novabrowse Git
repository and configured the `chromosome_data.json` and
`novabrowse_config.yaml` files.

It will make the directories `1_subject_sequences`, `2_subject_blastdb`,
`3_query_sequences`, and `4_blast_results` from the Git repository's
top-level directory available inside the Docker container (read/write).
It also makes the `chromosome_data.json` file available inside the
container (read-only), including any modifications you may have made to
it.

Fill out the value for the `ENTREZ_EMAIL_ENV` variable in the
`docker-compose.yml` file. The value should be thu email address that
you will use when making requests to NCBI.

## Basic Usage

To run, the `novabrowse_1.0.ipynb` notebook,

1.  change into the `docker` subdirectory of this Git repository,

2.  build and run the container

    ``` shell
    docker compose up --build
    ```

The generated output files will be available in the `novabrowse_output`
directory.

## A note about caching

To speed up repeated runs, the Docker setup caches downloaded NCBI data
in a persistent Docker volume named `novabrowse_ncbi_cache`. This cache
is used to store data downloaded from NCBI, so that subsequent runs do
not need to re-download the same data. All calls to the `Entrez.efetch`
and `Entrez.esearch` functions from the Biopython library will use this
cache.

The size of the cache is limited to 500 MB, or to the value of the
`ENTREZ_CACHE_SIZE_MB` variable in the `docker-compose.yml` file, if
set. You may want to increase this limit if you are working with a large
number of sequences, or with large individual requests (e.g.,
downloading large genomes). A single run of the default
`novabrowse_1.0.ipynb` notebook uses about 75 MB of cache space.

Setting the `ENTREZ_USE_CACHE` variable in the `docker-compose.yml` file
to `false` will disable the use of the cache entirely. Doing so will not
clear the existing cache, but will cause all NCBI data to be
re-downloaded on each request for the duration of the run.

The cache volume can be removed using the command

``` shell
docker volume rm novabrowse_ncbi_cache
```

or

``` shell
docker compose down -v
```
