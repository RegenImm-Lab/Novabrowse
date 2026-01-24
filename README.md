# <img src="images/novabrowse_logo.svg" alt="Novabrowse Logo" width="400">

**An interactive BLAST results interpretation tool for multi-species high-resolution synteny analysis, chromosomal rearrangement investigation, orthologs identification and gene signal discovery.**

## Table of Contents

- [Core Capabilities](#core-capabilities)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start & Tutorial](#quick-start--tutorial)
- [Configuration Reference](#configuration-reference)
- [General Features](#general-features)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Citation](#citation)
- [Contributing](#contributing)

## Core Capabilities

- **Multi-species synteny analysis** - Compare gene order conservation across multiple species simultaneously with interactive ribbon plots connecting orthologous genes across chromosomes
- **Gene signal discovery** - Identify unannotated genes in genomic regions through distance-based HSP clustering, revealing gene units missed by standard annotation pipelines
- **Coverage visualization** - View alignment coverage as identity-color-coded bars positioned along query sequences, showing both extent and quality of matches

## Prerequisites

### 1. Python 3.8+

Download from [python.org](https://www.python.org/downloads/)

### 2. Jupyter Notebook Environment

Novabrowse pipeline runs in a Jupyter Notebook, so you need a compatible program, for example:

- [VS Code](https://code.visualstudio.com/) with the [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)

### 3. <a href="https://www.ncbi.nlm.nih.gov/" target="_blank">NCBI</a> (https://www.ncbi.nlm.nih.gov/) BLAST+ Command Line Tools

BLAST+ must be installed and available in your system PATH.

**Option A: Conda (Recommended)**
```bash
conda install -c bioconda blast
```

**Option B: Manual Installation**
1. Download from [NCBI FTP](https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/)
2. Install and add to system PATH

### 4. NCBI Entrez Email

NCBI requires an email address for Entrez API access (needed for sequence retrieval requests).
- You can create the account at [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account/)


## Installation

1. **Download the repository**

   **Option A: Clone with Git**
   ```bash
   git clone https://github.com/RegenImm-Lab/Novabrowse.git
   ```

   **Option B: [Download ZIP](https://github.com/RegenImm-Lab/Novabrowse/archive/refs/heads/main.zip)** and extract it

2. **Install Python dependencies**

   Open a terminal in the project folder and run:
   ```bash
   pip install -r requirements.txt
   ```

   This installs Biopython and certifi (for SSL certificate handling).

   > **Windows note:** If `pip` doesn't work, try `py -m pip install -r requirements.txt` instead.

## Quick Start

In Novabrowse:
- **Query species** - the species whose genes you want to search for (your genes of interest)
- **Subject species** - the species you search against to find homologous matches

### 1. Prepare subject species files

Novabrowse supports both transcriptome and genome analysis. For each subject species, you'll need:

- **GTF annotation file** (Gene Transfer Format) - contains gene coordinates, names, and transcript information. The GTF must follow NCBI formatting conventions, but doesn't have to be downloaded from NCBI.
- **FASTA sequence file** - either transcriptome (`rna.fna`) or genome (`genomic.fna`) depending on your analysis needs.

For this tutorial, we'll use three fungal species from NCBI:

| Species | NCBI Link |
|---------|-----------|
| *Saccharomyces cerevisiae* | [Open](https://www.ncbi.nlm.nih.gov/datasets/taxonomy/4932/) |
| *Schizosaccharomyces pombe* | [Open](https://www.ncbi.nlm.nih.gov/datasets/taxonomy/4896/) |
| *Candida albicans* | [Open](https://www.ncbi.nlm.nih.gov/datasets/taxonomy/5476/) |

These files (GTF annotations and transcripts for all three species, plus the genome for *S. cerevisiae*) are already included in `1_subject_sequences/`. Below we explain how they were downloaded, which you can follow to add your own species or update the existing files.

**How to download from NCBI:**

- The image below shows *S. cerevisiae* as an example. When downloading assemblies from NCBI, you can choose the source (RefSeq or GenBank) based on your specific research needs.

<img src="images/how_to_download.png" alt="How to download from NCBI" style="margin-left: 20px;">

Place the downloaded files in:
```
1_subject_sequences/<custom_name>/<assembly>/
├── genomic.gtf       # Required: GTF annotation file
├── rna.fna           # For transcriptome analysis (exact filename required)
└── *_genomic.fna     # For genome analysis (must contain "_genomic" in filename)
```

> **Note:** The transcriptome file **must** be named exactly `rna.fna`. Genome files **must** contain `_genomic` in the filename (e.g., `GCF_000146045.2_R64_genomic.fna`).

Example for *S. cerevisiae*:
```
1_subject_sequences/s_cerevisiae/GCF_000146045.2/
├── genomic.gtf
├── rna.fna
└── GCF_000146045.2_R64_genomic.fna
```

### 2. Create subject species BLAST databases

Open `make_blastdb.ipynb` and edit the second cell to add your species, then run the notebook.
```python
run_makeblastdb(
    "1_subject_sequences\\<custom_name>\\<assembly>\\rna.fna",
    "nucl",
    "2_subject_blastdb\\<custom_name>_<assembly>"
)
```

Example for *S. cerevisiae*:
```python
run_makeblastdb(
    "1_subject_sequences\\s_cerevisiae\\GCF_000146045.2\\rna.fna",
    "nucl",
    "2_subject_blastdb\\s_cerevisiae_GCF_000146045.2"
)
```

### 3. Generate chromosome data file

Open `get_chromosome_info.ipynb` and add your species to `ASSEMBLY_MAPPING`:
   ```python
   ASSEMBLY_MAPPING = {
       '<custom_name>': '<assembly>',
   }
   ```

   Example for *S. cerevisiae*:
   ```python
   ASSEMBLY_MAPPING = {
       's_cerevisiae': 'GCF_000146045.2',
   }
   ```

Then run the notebook. It will query NCBI for chromosome accessions and lengths for each species and save the results to `chromosome_data.json`.

This file is used for mapping genes onto chromosomes.

**Important:** Both query and subject species must be included. If NCBI doesn't have chromosome information for a species, you'll need to add it manually to `chromosome_data.json`.

### 4. Configure Novabrowse

#### Open the main notebook

Open `novabrowse_1.0.ipynb`. This is the main notebook that:
1. Downloads query species sequences for your specified genomic region
2. Runs BLAST searches against your subject species
3. Generates interactive HTML result files

#### Set up NCBI Entrez email from query sequence retrieval

By default the pipeline reads your email from the `ENTREZ_EMAIL_ENV` environment variable. Choose one of these methods:

**Option A: Set system environment variable (Recommended)**

This keeps your email out of the code and works automatically.

*Windows (Command Prompt):*
```cmd
setx ENTREZ_EMAIL_ENV "your.email@example.com"
```

*Windows (PowerShell):*
```powershell
[System.Environment]::SetEnvironmentVariable("ENTREZ_EMAIL_ENV", "your.email@example.com", "User")
```

*macOS/Linux:*
```bash
echo 'export ENTREZ_EMAIL_ENV="your.email@example.com"' >> ~/.bashrc
source ~/.bashrc
```

> **Note:** After setting the environment variable, restart your terminal/IDE for changes to take effect.

**Option B: Set directly in notebook**

Alternatively, in the second code cell of the main Novabrowse notebook, replace the environment variable line with your email:
```python
Entrez.email = "your.email@example.com"  # Replace with your email
```

> **Warning:** If you use Option B and plan to share your code publicly, remember to remove your email before committing.


## Tutorial 1: Detecting Orthologs Across Species

This tutorial demonstrates how to identify orthologous genes across multiple species using synteny analysis. You'll search for orthologs of a target gene and the genes flanking it on both sides, then visualize their chromosomal positions across species.

**What you'll learn:**
- How to define a genomic region of interest in the query species
- Configure BLAST searches against multiple subject species
- Interpret the resulting synteny visualization

### 1. Setting up a query
**In this example scenario:** We'll examine the *ACT1* locus (encoding actin) in *S. cerevisiae* and find its orthologus loci in *S. pombe* and *C. albicans*.

To analyze a genomic region, first identify the chromosome and coordinates of your region of interest.

To find coordinates for the *ACT1* gene locus in *S. cerevisiae*:
1. Search for *S. cerevisiae* [*ACT1*](https://www.ncbi.nlm.nih.gov/gene/850504) gene on NCBI

<img src="images/how_to_get_genomic_region.png" alt="How to get genomic region" style="margin-left: 20px;">

2. Find the genomic location: `Chromosome: VI; NC_001138.5 (53260..54696, complement)`


Configure the first cell:
```python
title = "ACT1_synteny" # Prefix for output files from this run

query_sequences_list = [
    {
        'query_species': 's_cerevisiae',           # Species name (must match ASSEMBLY_MAPPING key)
        'protein_sources': ('NP_','XP_'),          # See note Protein Source Filtering
        'show_only_best_matches': 'True',          # Allowed values: 'True', 'False', 'Both'
        'retrieved_sequences': {
            'download_from_NCBI': True,            # Fetch sequences from NCBI
            'chromosome': 'VI',                    # Allowed types: '6', '6q', 'VI' or 'NC_001138.5'
            'start_position': 53260,               # Region start coordinate
            'end_position': 54696,                 # Region end coordinate
            'genes_upstream': 5,                   # Include 5 genes before the region
            'genes_downstream': 5,                 # Include 5 genes after the region
        },
    },
]
```
1. Use chromosome `VI` and the corresponding start `53260` and end `54696` coordinates of *ACT1*.
2. Set upstream/downstream genes to include flanking genes (e.g., 5 each)

> **Note:** The `query_species` value must match the name you used in `ASSEMBLY_MAPPING` (step 3) and your folder name in `1_subject_sequences/`.

> **Chromosome identifiers:** You can use traditional chromosome names (`'VI'`, `'2'`, `'2p'`, `'II'`) or NCBI accession identifiers (`'NC_001138.5'`, `'NC_032095.1'`). Accession identifiers support version-flexible matching - for example, `'NC_032095'` will match `'NC_032095.1'`. Use accession identifiers when traditional names don't work or for more precise targeting.

> **Adaptive range fetching:** The `genes_upstream` and `genes_downstream` parameters use adaptive range searching. Novabrowse automatically expands the search window to find exactly the requested number of genes, regardless of gene density in the region.

### 2. Configure BLAST settings

Choose which BLAST algorithm(s) to use:
- `blastn` - nucleotide vs nucleotide (best for closely related species)
- `tblastn` - protein vs translated nucleotide (most common for cross-species analysis)
- `tblastx` - translated nucleotide vs translated nucleotide (for divergent species)

You can enable multiple types at once - a **separate result file will be generated for each combination** of BLAST type and database type:

```python
blast_settings = {
    'blast_type': ['tblastn', 'blastn'],  # Two result files per species/database combination
    'blast_options': '-outfmt 0 -num_threads 48'
}
```

For example, with 2 subject species configured with `'type': ['transcriptome', 'genome']` and 2 BLAST types, you'll get 8 total result files (2 species × 2 database types × 2 BLAST types).

### 3. Select subject species

Configure which species to search against. Each species can be configured separately:

**Subject Species Parameters:**

| Parameter | Description |
|-----------|-------------|
| `enabled` | `True` to include this species in BLAST search, `False` to skip |
| `maximum_evalue` | E-value threshold - only hits with e-value ≤ this value are kept (e.g., `1e-10`) |
| `minimum_score` | Minimum BLAST bit score - hits below this score are filtered out (0 = no minimum) |
| `additional_blast_parameters` | Extra BLAST command-line options for this species only (e.g., `'-word_size 11'`) |
| `type` | Database type(s) as list: `['transcriptome']`, `['genome']`, or `['transcriptome', 'genome']` for both |

> **Note:** Per-species `maximum_evalue` and `minimum_score` settings override the general values in `blast_options`.

```python
subject_species = {
   's_cerevisiae': {
       'enabled': False,        # Skip searching against query species
       'maximum_evalue': 1e-10,
       'minimum_score': 0,
       'additional_blast_parameters': '',
       'type': ['transcriptome']
   },
   's_pombe': {
       'enabled': True,         # Search this species
       'maximum_evalue': 1e-10,
       'minimum_score': 0,
       'additional_blast_parameters': '',
       'type': ['transcriptome']
   },
   'c_albicans': {
       'enabled': True,         # Search this species
       'maximum_evalue': 1e-10,
       'minimum_score': 0,
       'additional_blast_parameters': '',
       'type': ['transcriptome']
   },
}
```
> **Note:** When using `['transcriptome', 'genome']`, separate result files are generated for each database type.
> **Tip:** Set the query species to `enabled: False` to avoid self-hits. You typically want to search other species, not your query species against itself.

### 4. Map species to NCBI organism names

Map each species name to its NCBI organism name (used for Entrez queries and display names in results):

```python
species_to_orgn = {
    's_cerevisiae': 'Saccharomyces cerevisiae[ORGN]',
    's_pombe': 'Schizosaccharomyces pombe[ORGN]',
    'c_albicans': 'Candida albicans[ORGN]',
}
```


### 5. Run all notebook cells sequentially

### 6. Find results in the project root folder as interactive HTML files

Example output files:
- `Novabrowse_ACT1_synteny_s_cerevisiae_blastn_best_matches.html` - blastn results
- `Novabrowse_ACT1_synteny_s_cerevisiae_tblastn_best_matches.html` - tblastn results

Example how the tblastn output file should look:

<img src="images/sample_file.png" alt="How to download from NCBI" style="margin-left: 20px;">


<br>


## Tutorial 2: Using Custom Sequences and Gene Signal Discovery


<br><br><br><br>

## Configuration Reference

This section provides detailed documentation for all configuration parameters. For usage examples, see the tutorials above.

### Query Configuration (`query_sequences_list`)

| Parameter | Type | Description |
|-----------|------|-------------|
| `query_species` | string | Species name (must match `ASSEMBLY_MAPPING` key and folder name) |
| `protein_sources` | tuple | Filter genes by accession prefix. See [Protein Source Prefixes](#protein-source-prefixes) |
| `show_only_best_matches` | string | `'True'` (best match only), `'False'` (all matches), or `'Both'` (generates two separate HTML files) |

#### Retrieved Sequences (`retrieved_sequences`)

| Parameter | Type | Description |
|-----------|------|-------------|
| `download_from_NCBI` | bool | Set `False` to use only custom sequences |
| `chromosome` | string | Chromosome name (`'VI'`, `'2'`, `'2p'`) or NCBI accession (`'NC_001138.5'`). Version-flexible matching supported |
| `start_position` | int | Region start coordinate |
| `end_position` | int | Region end coordinate (must be > start_position) |
| `genes_upstream` | int | Number of flanking genes before region (uses adaptive range searching) |
| `genes_downstream` | int | Number of flanking genes after region (uses adaptive range searching) |

> **Note:** NCBI API rejects queries larger than ~8-10 MB. Reduce region size or gene counts if you get "HTTP Error 400".

#### Custom Sequences (`custom_sequences`)

Optional array for including user-provided sequences alongside NCBI data (e.g., from nanopore sequencing):

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique display name for results |
| `id` | string | ID for NCBI link generation |
| `description` | string | FASTA header description |
| `nucleotide_sequence` | string | DNA sequence |
| `protein_sequence` | string | Amino acid sequence |
| `chromosome` | string | Chromosome identifier |
| `strand` | string | `"1"` (forward) or `"-1"` (reverse) |
| `start_position` | string | Genomic start coordinate |
| `end_position` | string | Genomic end coordinate |

### BLAST Configuration

#### Gene Signal Discovery (`consider_one_gene`)

For genome searches (not transcriptomes), Novabrowse clusters nearby BLAST HSPs into gene units:

```python
consider_one_gene = 1050  # Maximum distance (bp) between HSPs to merge into one gene
```

HSPs within this distance are merged into a single entry with combined coverage. When BLASTing a transcript against a genome, HSPs correspond to exons and gaps between them are introns. Set this value larger than the largest intron in your species to ensure all exons from the same gene are grouped correctly.

#### BLAST Settings (`blast_settings`)

| Parameter | Type | Description |
|-----------|------|-------------|
| `blast_type` | list | Algorithm(s) to use: `['tblastn']`, `['blastn']`, `['tblastx']`, or combinations like `['tblastn', 'blastn']` |
| `blast_options` | string | Command-line options. `-outfmt 0` is required. `-num_threads` is auto-adjusted to available cores |

**BLAST algorithms:**
- `blastn` - nucleotide vs nucleotide (best for closely related species)
- `tblastn` - protein vs translated nucleotide (most common for cross-species)
- `tblastx` - translated nucleotide vs translated nucleotide (for divergent species)

### Subject Species Configuration (`subject_species`)

| Parameter | Type | Description |
|-----------|------|-------------|
| `enabled` | bool | `True` to include in analysis, `False` to skip |
| `maximum_evalue` | float | E-value threshold - hits above this are filtered out (e.g., `1e-10`) |
| `minimum_score` | int | Minimum bit score filter (`0` = no minimum) |
| `additional_blast_parameters` | string | Species-specific BLAST command-line options |
| `type` | list | Database type(s): `['transcriptome']`, `['genome']`, or `['transcriptome', 'genome']` for both |

> **Tip:** Set query species to `enabled: False` to avoid self-hits.

> **Output files:** Separate result files are generated for each combination of BLAST type × database type × species.

### Protein Source Prefixes

The `protein_sources` parameter filters genes by NCBI accession prefix:

| Prefix | Description |
|--------|-------------|
| `NP_` | RefSeq curated proteins (manually reviewed, highest quality) |
| `XP_` | RefSeq predicted proteins (computational models) |
| `XM_` | Predicted mRNA sequences (not experimentally validated) |
| `XR_` | RefSeq non-coding RNA |
| `YP_` | RefSeq provisional proteins |
| `WP_` | Non-redundant RefSeq proteins |
| `CAA_` | EMBL (European Molecular Biology Laboratory) entries |
| `BAD_` | DDBJ (DNA Data Bank of Japan) entries |

Only genes with at least one product matching these prefixes will be retrieved.

### Gene Name Assignment

When retrieving genes from NCBI, Novabrowse assigns display names using this fallback hierarchy:
1. Official gene symbol (e.g., `ACT1`)
2. Locus tag identifier (e.g., `CAALFM_C700260CA`)
3. First available synonym
4. `"Uncharacterized"` if no identifiers available

## General Features

#### **BLAST Integration**
- **Multiple BLAST algorithms** - Support for BLASTn, tBLASTn, and tBLASTx with independent configuration per subject species
- **Automated NCBI retrieval** - Direct integration with NCBI E-utilities API for automatic gene sequence downloads
- **Custom sequence support** - Incorporate user-provided sequences (e.g., from nanopore sequencing) alongside NCBI data
- **Flexible filtering** - Configure E-value thresholds and bit score cutoffs independently per species
- **Automatic quality filtering** - Filters out discontinued and obsolete gene entries from NCBI
- **Gene signal discovery** - Detect unannotated genes in genome searches through HSP clustering (see [Configuration Reference](#gene-signal-discovery-consider_one_gene))
- **Smart gene naming** - Hierarchical fallback for display names when official nomenclature is unavailable

#### **Interactive Visualization**
- **High-resolution chromosomal maps** - Interactive chromosome visualizations showing precise gene positions with support for both single chromosomes and multi-arm configurations
- **Dynamic filtering system** - Filter by gene names, conservation levels, genomic coordinates, or match quality with real-time statistical updates
- **Isoform management** - Automatic consolidation of transcript isoforms with expandable views showing all variants and their alignment statistics
- **Coordinate-based highlighting** - Focus analysis on specific genomic regions through visual highlighting or selective display of genes within defined coordinate ranges

#### **Analysis Features**
- **Transcriptome and genome searches** - Search against both annotated transcriptomes (using GTF files) or raw genomes (with automatic HSP clustering)
- **Multi-arm chromosome support** - Proper coordinate transformation for chromosomes represented as separate p and q arms in assemblies
- **Alignment quality metrics** - Track coverage percentage, identity (both total and local), bit scores, E-values, and HSP counts
- **Publication-ready export** - Generate SVG files containing complete table structure, chromosome maps, and active ribbon visualizations for direct use in publications or further editing

#### **User Experience**
- **All-in-one HTML output** - Self-contained interactive HTML files with embedded JavaScript for dynamic filtering and visualization without requiring server-side processing
- **Batch processing** - Process multiple genomic regions and species within single execution runs
- **Column customization** - Toggle visibility and reorder data columns including coordinates, lengths, alignment statistics, and chromosome visualizations
- **Drag-and-drop organization** - Reorder subject species columns to facilitate comparative analysis

## Documentation

### Interactive Controls Reference

The Novabrowse HTML output includes numerous interactive buttons organized into functional categories. Below is a complete reference for all available controls:

#### Download
- **Save as SVG** - Exports the current table view, including visible columns, chromosome visualizations, and active ribbons, as a vector SVG file ready for publication or editing in vector graphics software

#### View Controls
- **Ribbon plot** - Displays curved ribbons connecting homologous genes across species chromosomes, providing visual synteny relationships. Useful for quickly identifying conserved genomic neighborhoods
- **Ribbon settings** - Opens configuration panel to customize ribbon appearance (color, opacity, style) and enable selective display for specific genes
- **Normalize chromosomes** - When enabled, scales all chromosome visualizations to equal height for easier cross-species comparison. When disabled, chromosomes are sized proportionally to their actual lengths
- **Chrm height = Table height** - Controls chromosome column behavior. When active, chromosome visualizations scroll with the table. When inactive, chromosomes use sticky positioning and remain visible during scrolling
- **Equalize 1st row** - Adjusts species header widths to match the widest column, creating uniform spacing across the first row
- **Equalize 3rd row** - Standardizes data column widths within each species to match the widest column in that section
- **Color legend** - Toggles visibility of the match percentage color scale reference (shows identity percentage color coding from 0% to 120%+)
- **Matches** - Displays match count statistics in species headers (e.g., "Matches: 9" showing how many query genes have hits)
- **Score & E-value** - Shows BLAST filtering parameters in species headers (minimum score and maximum E-value thresholds used)
- **abc/123** - Controls visibility of alphabetical/numerical sorting buttons in the query species column
- **ID** - Toggles display of NCBI gene IDs in parentheses next to gene names (e.g., "foxp3 (12345)")
- **Transcripts** - Shows/hides transcript isoform counts and expandable transcript details for each gene match
- **Title wrap** - Enables text wrapping in species header cells to prevent horizontal overflow of long species names

#### Filters
- **Filter** (Gene name filter) - Activates filtering based on comma-separated gene names entered in the text box. Displays only matching genes and their homologs across all species
- **Gene filter** - Toggles visibility of the gene name text input box (useful for saving screen space when not actively filtering by gene names)
- **Chrm filter** - Shows/hides the coordinate range inputs and chromosome selection dropdowns used for position-based filtering
- **At least 1 match** - Displays only genes that have at least one homolog identified in any of the visible subject species (hides genes with no matches anywhere)
- **Full conservation** - Shows only genes with matches detected in every visible subject species, identifying universally conserved genes
- **True coordinates** - For multi-arm chromosomes (p/q arms), switches between cumulative positions (combined arms) and true per-arm coordinates. Useful for accurately identifying positions on specific chromosome arms
- **Hide 2nd match genes** - Removes secondary/paralog matches from the table, keeping only the highest-scoring match per gene per species. Simplifies view when focusing on primary orthologs
- **Filter** (Span filter) - Restricts table to show only query species genes falling within the specified start/end coordinate range
- **Highlight** - Applies yellow background highlighting to genes within the specified coordinate range across all species, allowing visual focus without hiding other genes
- **Keep** - More restrictive than Highlight - displays only genes that have matches on the selected chromosomes within the defined coordinate span. Removes entire chromosomes not selected via checkboxes

#### Species Controls
Species toggle buttons allow you to show or hide individual subject species columns. Drag-and-drop functionality enables reordering of species columns for customized comparative analysis.

#### Column Visibility Toggles
- **#** - Row numbering for easy reference and navigation through large gene lists
- **Gene (query)** - Query species gene names with NCBI links. Hiding this column removes the source gene identifiers
- **Gene (subject)** - Subject species gene names and IDs. Toggle to focus on other metrics when gene names are not needed
- **Start** - Genomic start coordinates for each gene. Useful for precise location mapping
- **End** - Genomic end coordinates for each gene. Combined with Start, defines exact gene boundaries
- **Chrm #** - Chromosome assignments (e.g., "I", "2", "X"). Essential for identifying which chromosome each match is located on
- **DNA Length (%)** - Ratio of subject DNA length to query DNA length as percentage. Values >100% indicate the subject gene is longer than query
- **mRNA length (%)** - Ratio of subject mRNA/transcript length to query length. Helps identify size differences between orthologs
- **Best Total Identity (%)** - Highest identity percentage across all aligned segments for this gene pair. Measures overall sequence similarity
- **Best Local Identity (%)** - Highest identity percentage within a single HSP (local alignment). Can be higher than total identity for highly conserved domains
- **Coverage** - Visual bars showing which portions of the query sequence align to the subject, color-coded by identity percentage. Critical for identifying partial vs complete matches
- **# HSPs** - Number of High-scoring Segment Pairs (alignment segments) detected. Multiple HSPs may indicate exon structure or domain conservation
- **Query Length** - Length of the query protein/transcript in amino acids or nucleotides. Provides scale reference for coverage interpretation
- **Score** - BLAST bit score indicating alignment strength. Database-size independent metric for comparing match quality
- **E-value** - Expect value indicating statistical significance. Lower values indicate more significant matches (database-size dependent)
- **Chrm** - Chromosome visualization columns showing gene positions on scaled chromosome maps with ribbon connections

#### Table Sorting
- **123** - Sorts genes by their genomic coordinates (numerical position order). Maintains genes in chromosomal order as they appear in the genome
- **abc** - Sorts genes alphabetically by name. Useful for finding specific genes quickly or grouping gene families

#### Gene Selection
Click gene names in the Query Species column to add or remove them from the filter text box for quick multi-gene selection. Use the checkbox beside each gene name to control its ribbon visibility - checked genes display their synteny ribbons, while unchecked genes hide their connections. The master checkbox in the header selects/deselects all genes simultaneously.

## Troubleshooting

### "HTTP Error 400" from NCBI
- Reduce the genomic region size or number of upstream/downstream genes
- NCBI API has limits on query size (~8-10 MB)

### "makeblastdb not found"
- Ensure BLAST+ is installed and in your PATH
- Try running `makeblastdb -version` to verify

### No genes found
- Check that the chromosome format matches NCBI naming
- Verify genomic coordinates are correct for your assembly version

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

If you use Novabrowse in your research, please cite:
```
[Citation information to be added]
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.