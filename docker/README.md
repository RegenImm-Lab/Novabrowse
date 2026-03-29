# Novabrowse with Docker and Apptainer

Run Novabrowse synteny analysis in a Docker or Apptainer container. All dependencies are included, making it easy to set up and run consistently across different environments, including HPC clusters.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Getting the Image](#getting-the-image)
  - [Docker](#docker)
  - [Apptainer](#apptainer)
- [Try It Quickly](#try-it-quickly)
- [Setup](#setup)
  - [1. Prepare subject species files](#1-prepare-subject-species-files)
  - [2. Understanding the Docker workflow](#2-understanding-the-docker-workflow)
  - [3. Configure assembly mapping](#3-configure-assembly-mapping)
  - [4. Create BLAST databases](#4-create-blast-databases)
  - [5. Set up NCBI email](#5-set-up-ncbi-email)
  - [6. Generate chromosome data](#6-generate-chromosome-data)
  - [7. Configure analysis parameters](#7-configure-analysis-parameters)
  - [8. Running the analysis](#8-running-the-analysis)
  - [9. Find results](#9-find-results-in-the-output-folder-as-html-files)
- [Using custom YAML config files](#using-custom-yaml-config-files)
- [Caching](#caching)
- [Environment variables reference](#environment-variables-reference)

## Prerequisites

- Basic knowledge of using the command line.
- Docker installed on your machine (with the Docker service up and
  running), if you want to build and/or run the container locally.
- Apptainer installed on your machine, if you want to run the pre-built
  Docker image using Apptainer instead of Docker.
- An NCBI account — you can create one at [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account/). The email associated with your account is used to identify your API requests (see [step 5](#5-set-up-ncbi-email)).
- This repository cloned from GitHub:
  - **Option A: Clone with Git**
    ```bash
    git clone https://github.com/RegenImm-Lab/Novabrowse.git
    ```
  - **Option B: [Download ZIP](https://github.com/RegenImm-Lab/Novabrowse/archive/refs/heads/main.zip)** and extract it

## Getting the Image

### Docker

Two options — build locally or pull pre-built:

**Option A: Build locally**

From the repository's top-level directory:

``` shell
docker build -t novabrowse -f docker/Dockerfile docker/
```

**Option B: Pull pre-built image**

``` shell
docker pull ghcr.io/regenimm-lab/novabrowse:latest
```

Please have a look at the GitHub Container Registry page for this
repository for the latest available image tags:
https://github.com/RegenImm-Lab/Novabrowse/pkgs/container/novabrowse

### Apptainer

Pull the pre-built image directly from the registry and convert it to an Apptainer SIF file:

``` shell
apptainer pull novabrowse.sif docker://ghcr.io/regenimm-lab/novabrowse:latest
```

If you built the Docker image locally instead, convert it with:

``` shell
apptainer build novabrowse.sif docker-daemon://novabrowse:latest
```

## Try It Quickly

The repository comes pre-configured with three example species (*S. cerevisiae*, *S. pombe*, *C. albicans*) with BLAST databases and chromosome data included. To run the example analysis, set `entrez_email: "you@email.com"` in `novabrowse_config.yaml` using your [NCBI account](https://www.ncbi.nlm.nih.gov/account/) email and run:
```shell
docker run -t -v "$(pwd):/data" novabrowse novabrowse_1.0.ipynb
```
Results will be in the `output/` folder as HTML files.

To learn how to add your own species and configure analyses, follow the [Setup](#setup) guide below.

## Setup

In Novabrowse:
- **Query species** - the species whose genes you want to search for (your genes of interest)
- **Subject species** - the species you search against to find homologous matches

### 1. Prepare subject species files

Novabrowse supports both transcriptome and genome analysis. For each subject species, you'll need:

- **GTF annotation file** (Gene Transfer Format) - contains gene coordinates, names, and transcript information. The GTF must follow NCBI formatting conventions, but can come from any source (e.g., NCBI, Ensembl, or your own custom annotations).
- **FASTA sequence file** - either transcriptome (`rna.fna`) or genome (`genomic.fna`) depending on your analysis needs. These can also be custom assemblies as long as they match the GTF.

Place the downloaded files in:
```
1_subject_sequences/<custom_name>/<assembly>/
├── genomic.gtf       # Required: GTF annotation file
├── rna.fna           # For transcriptome analysis (exact filename required)
└── *_genomic.fna     # For genome analysis (must contain "_genomic" in filename)
```

> **Note:** The transcriptome file **must** be named exactly `rna.fna`. Genome files **must** contain `_genomic` in the filename (e.g., `GCF_000146045.2_R64_genomic.fna`).

For instructions on how to download these files from NCBI, see [How to download subject species sequences from NCBI](../README.md#subject-species-used-in-this-tutorial) in Tutorial 1.

### 2. Understanding the Docker workflow

Novabrowse is built around three Jupyter notebooks: `make_blastdb.ipynb` creates BLAST databases, `get_chromosome_info.ipynb` retrieves chromosome data from NCBI, and `novabrowse_1.0.ipynb` runs the main analysis. The Docker container converts these notebooks to Python scripts and runs them automatically. In Docker and Apptainer, all analysis parameters are set in a single YAML file (`novabrowse_config.yaml`, located in the repository's top-level directory), which is easier to edit with command line based text editors (e.g., `nano`, `vim`, `emacs`) than the lengthy `.ipynb` notebook files.

You can also edit the `.ipynb` notebook files directly if you need to customize behavior beyond what the YAML file provides.

> **Note:** If `novabrowse_config.yaml` is not found, the notebooks fall back to their default values.

### 3. Configure assembly mapping

Assembly mapping links each subject species to its assembly accession and the FASTA files you placed in step 1. This is how Novabrowse knows which BLAST databases to create and which assemblies to query for chromosome data.

Add each species with its assembly accession and database entries. Each database entry specifies the FASTA file, its type (`nucl` or `prot`), and whether it is a `genome` or `transcriptome` database.

For example, if you placed *S. cerevisiae* files in step 1 like this:

```
1_subject_sequences/s_cerevisiae/GCF_000146045.2/
├── genomic.gtf
├── rna.fna
└── GCF_000146045.2_R64_genomic.fna
```

The corresponding `ASSEMBLY_MAPPING` entry in `novabrowse_config.yaml` would be:

```yaml
ASSEMBLY_MAPPING:
  s_cerevisiae:
    assembly_acc: "GCF_000146045.2"
    databases:
      - fasta_file: "rna.fna"
        fasta_file_type: "nucl"
        type: "transcriptome"
      - fasta_file: "GCF_000146045.2_R64_genomic.fna"
        fasta_file_type: "nucl"
        type: "genome"
```

### 4. Create BLAST databases

All commands below are run from the repository's **top-level directory**.

This step automatically creates BLAST databases for all species and database types defined in `ASSEMBLY_MAPPING`, saving them to `2_subject_blastdb/`. Make sure `ASSEMBLY_MAPPING` is configured (step 3) and the corresponding FASTA files are in place (step 1).

**Docker:**
``` shell
docker run -t -v "$(pwd):/data" novabrowse make_blastdb.ipynb
```

**Apptainer:**
``` shell
apptainer run -e --bind "$(pwd):/data" novabrowse.sif make_blastdb.ipynb
```

### 5. Set up NCBI email

The remaining steps query NCBI and require an email address to identify requests. If you don't have an NCBI account yet, create one at [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account/). There are three ways to provide it:

**Option A: In the YAML config file (`novabrowse_config.yaml`)**

Set the `entrez_email:` field in `novabrowse_config.yaml`:
```yaml
entrez_email: "you@email.com"
```

**Option B: Pass from your OS environment variable**

If you have `ENTREZ_EMAIL_ENV` already set in your OS (see [how to set it](../README.md#3-set-up-ncbi-email)), pass it through when running the container:
``` shell
docker run -t -v "$(pwd):/data" -e ENTREZ_EMAIL_ENV novabrowse novabrowse_1.0.ipynb
```

**Option C: Set explicitly in the run command**

Set `-e ENTREZ_EMAIL_ENV="you@email.com"` when running the container.

> **Note:** If both the environment variable and the YAML config (`novabrowse_config.yaml`) are set, the environment variable takes priority.

### 6. Generate chromosome data

**Docker:**
``` shell
docker run -t -v "$(pwd):/data" novabrowse get_chromosome_info.ipynb
```

**Apptainer:**
``` shell
apptainer run -e --bind "$(pwd):/data" novabrowse.sif get_chromosome_info.ipynb
```

This queries NCBI for chromosome accessions and lengths for each species in `ASSEMBLY_MAPPING` and saves the results to `chromosome_data.json`.

> **Important:** `chromosome_data.json` must contain entries for all species used in the analysis (both query and subject). If NCBI doesn't have chromosome information for a species, you'll need to add it manually (see [Chromosome Data Format](../README.md#chromosome-data-format) for the expected structure).

### 7. Configure analysis parameters

Edit `novabrowse_config.yaml` to define analysis parameters: the genomic region of interest in the query species, which subject species to search against, and BLAST search parameters.

In this example, we set up a search for orthologs of the *ACT1* gene in *S. cerevisiae*, searching against *S. pombe* (transcriptome) and *S. cerevisiae* itself (transcriptome and genome).

```yaml
title: "ACT1_orthology"                    # Prefix for output files

query_sequences_list:
  - query_species: "s_cerevisiae"          # Must match ASSEMBLY_MAPPING key
    protein_sources: ["NP_", "XP_"]        # Protein accession prefixes to include
    show_only_best_matches: "True"         # 'True', 'False', or 'Both'
    retrieved_sequences:
      download_from_NCBI: true             # Fetch sequences from NCBI
      chromosome: "VI"                     # E.g. '6', '6q', 'VI', or 'NC_001138.5'
      start_position: 53260               # Region start coordinate
      end_position: 54696                 # Region end coordinate
      genes_upstream: 5                   # Include 5 genes before the region
      genes_downstream: 5                # Include 5 genes after the region

# Max distance (bp) between genomic BLAST HSPs to merge into one gene unit
consider_one_gene: 1050

blast_settings:
  blast_type: ["tblastn", "blastn"]       # Search algorithm(s)
  blast_options: "-outfmt 0 -num_threads 48"  # BLAST command-line options

subject_species:
  s_pombe:
    enabled: true                         # Include in search
    maximum_evalue: 1e-10                 # E-value threshold
    minimum_score: 0                      # Minimum bit score (0 = no minimum)
    additional_blast_parameters: ""       # Extra BLAST parameters for this species
    type: ["transcriptome"]               # Transcriptome only
  s_cerevisiae:
    enabled: false                        # Skip (query species)
    maximum_evalue: 1e-10
    minimum_score: 0
    additional_blast_parameters: ""
    type: ["transcriptome", "genome"]     # Both transcriptome and genome
```

To include custom sequences alongside (or instead of) NCBI-retrieved sequences, add them under `custom_sequences` in `query_sequences_list`:

```yaml
query_sequences_list:
  - query_species: "s_cerevisiae"
    custom_sequences:
      - name: "LEU2_custom"                # Unique name for this sequence
        id: "850342"                       # NCBI gene ID (used for link generation)
        description: ">LEU2 custom seq"    # FASTA header
        nucleotide_sequence: "ATGACTAATC..." # Single line, no line breaks
        protein_sequence: "MTITKDHLIR..."  # Single line, no line breaks
        chromosome: "III"
        strand: "1"
        start_position: "91391"
        end_position: "92480"
```

For detailed explanations of each parameter and how to set up different types of analyses, see [Tutorial 1](../README.md#tutorial-1-detecting-orthologs-across-species) and [Tutorial 2](../README.md#tutorial-2-using-custom-sequences-and-gene-signal-discovery), which walk through the full process from downloading subject species files to rendering the final output. A complete [Parameters Reference](../README.md#parameters-reference) is also available. Note that the tutorials reference the main notebook's (`novabrowse_1.0.ipynb`) first cell configuration; for Docker and Apptainer, these same parameters are set in the YAML file (`novabrowse_config.yaml`).

### 8. Running the analysis

**Docker:**
``` shell
docker run -t -v "$(pwd):/data" novabrowse {notebook_filename}
```

> Example: `docker run -t -v "$(pwd):/data" novabrowse novabrowse_1.0.ipynb`

**Apptainer:**
``` shell
apptainer run -e --bind "$(pwd):/data" novabrowse.sif {notebook_filename}
```

> Example: `apptainer run -e --bind "$(pwd):/data" novabrowse.sif novabrowse_1.0.ipynb`

### 9. Find results in the `output/` folder as HTML files

## Using custom YAML config files

By default, Novabrowse reads `novabrowse_config.yaml` from the repository's top-level directory. You can point to a different YAML file using the `NOVABROWSE_CONFIG` environment variable. This is useful for keeping a separate config file for each analysis, so you have a record of the exact parameters used in each run.

**Docker:**
``` shell
-e NOVABROWSE_CONFIG={path_to_yaml}
```

> Example: `docker run -t -v "$(pwd):/data" -e NOVABROWSE_CONFIG=./custom_analysis.yaml novabrowse novabrowse_1.0.ipynb`

**Apptainer:**
``` shell
--env NOVABROWSE_CONFIG={path_to_yaml}
```

> Example: `apptainer run -e --bind "$(pwd):/data" --env NOVABROWSE_CONFIG=./custom_analysis.yaml novabrowse.sif novabrowse_1.0.ipynb`

## Caching

To speed up repeated runs, downloaded NCBI data is cached in the `tmp/ncbi_cache/` directory so that subsequent runs do not need to re-download the same data. A single run of the default `novabrowse_1.0.ipynb` notebook uses about 75 MB of cache space.

The cache size and behavior can be controlled with the `ENTREZ_CACHE_SIZE_MB` and `ENTREZ_USE_CACHE` environment variables. Disabling the cache will not clear existing cached data, but will cause all NCBI data to be re-downloaded for the duration of the run.

To clear the cache:

*macOS/Linux:*
``` shell
rm -rf tmp/ncbi_cache
```

*Windows (Command Prompt):*
``` cmd
rmdir /s /q tmp\ncbi_cache
```

*Windows (PowerShell):*
``` powershell
Remove-Item -Recurse -Force tmp\ncbi_cache
```

## Environment variables reference

Environment variables are passed with the `-e` flag. Docker does not remember previous `-e` values — every `docker run` creates a fresh container.

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `ENTREZ_EMAIL_ENV` | *(none)* | Email for NCBI API requests. Required if not set in YAML. | `-e ENTREZ_EMAIL_ENV="you@email.com"` |
| `NOVABROWSE_CONFIG` | `./novabrowse_config.yaml` | Using different YAML config file | `-e NOVABROWSE_CONFIG=./my_config.yaml` |
| `ENTREZ_CACHE_SIZE_MB` | `500` | Maximum NCBI cache size in MB | `-e ENTREZ_CACHE_SIZE_MB=1000` |
| `ENTREZ_USE_CACHE` | `true` | Set to `false` to disable NCBI data caching | `-e ENTREZ_USE_CACHE=false` |

**Full example with multiple options:**

``` shell
docker run -t -v "$(pwd):/data" -e ENTREZ_EMAIL_ENV="you@email.com" -e ENTREZ_CACHE_SIZE_MB=1000 novabrowse novabrowse_1.0.ipynb
```
