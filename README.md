# <img src="images/novabrowse_logo.svg" alt="Novabrowse Logo" width="400">

**An interactive BLAST results interpretation tool for multi-species high-resolution synteny analysis, chromosomal rearrangement investigation, orthologs identification and gene signal discovery.**

## Table of Contents

- [Core Capabilities](#core-capabilities)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start & Tutorial](#quick-start--tutorial)
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

### 4. [NCBI](https://www.ncbi.nlm.nih.gov/) Entrez Email

[NCBI](https://www.ncbi.nlm.nih.gov/) requires an email address for Entrez API access. This is used to identify your requests and allows [NCBI](https://www.ncbi.nlm.nih.gov/) to contact you if there are problems.

**Register (optional but recommended):**
- Create an [NCBI](https://www.ncbi.nlm.nih.gov/) account at [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account/)


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
   
   > **Windows note:** If `pip` doesn't work, try `py -m pip install -r requirements.txt` instead.

## Quick Start

In Novabrowse:
- **Query species** - the species whose genes you want to search for (your genes of interest)
- **Subject species** - the species you search against to find homologous matches

### 1. Prepare subject species files

Novabrowse supports both transcriptome and genome analysis. For each subject species, you'll need:

- **GTF annotation file** (Gene Transfer Format) - contains gene coordinates, names, and transcript information. The GTF must follow [NCBI](https://www.ncbi.nlm.nih.gov/) formatting conventions, but doesn't have to be downloaded from [NCBI](https://www.ncbi.nlm.nih.gov/).
- **FASTA sequence file** - either transcriptome (`rna.fna`) or genome (`genomic.fna`) depending on your analysis needs.

For this tutorial, we'll use three fungal species from [NCBI](https://www.ncbi.nlm.nih.gov/):

| Species | [NCBI](https://www.ncbi.nlm.nih.gov/) Link |
|---------|-----------|
| *Saccharomyces cerevisiae* | [Download](https://www.ncbi.nlm.nih.gov/datasets/taxonomy/4932/) |
| *Schizosaccharomyces pombe* | [Download](https://www.ncbi.nlm.nih.gov/datasets/taxonomy/4896/) |
| *Candida albicans* | [Download](https://www.ncbi.nlm.nih.gov/datasets/taxonomy/5476/) |

These example files (GTF annotations and transcripts for all three species, plus the genome for *S. cerevisiae*) are already included in the repository under `1_subject_sequences/`.

**Downloading from [NCBI](https://www.ncbi.nlm.nih.gov/):**

<img src="images/how_to_download.png" alt="How to download from NCBI" style="margin-left: 20px;">

<sub>When downloading assemblies from [NCBI](https://www.ncbi.nlm.nih.gov/), you can choose the source (RefSeq or GenBank) based on your specific research needs. The included examples were downloaded using **RefSeq** ([NCBI](https://www.ncbi.nlm.nih.gov/) Reference Sequence) assemblies, which are curated.</sub>

Place the downloaded files in:
```
1_subject_sequences/<custom_name>/<assembly>/
├── genomic.gtf      # Required: GTF annotation file
├── rna.fna          # For transcriptome analysis
└── genomic.fna      # For genome analysis
```

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

Open `get_chromosome_info.ipynb` and edit:

1. Set your [NCBI](https://www.ncbi.nlm.nih.gov/) Entrez email:
   ```python
   Entrez.email = "your.email@example.com"
   ```

2. Add your species to `ASSEMBLY_MAPPING`:
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

Then run the notebook. It will query [NCBI](https://www.ncbi.nlm.nih.gov/) for chromosome accessions and lengths for each species and save the results to `chromosome_data.json`.

This file is used for mapping genes onto chromosomes.

**Important:** Both query and subject species must be included. If [NCBI](https://www.ncbi.nlm.nih.gov/) doesn't have chromosome information for a species, you'll need to add it manually to `chromosome_data.json`.

### 4. Configure Novabrowse

Open `novabrowse_1.0.ipynb`. This is the main notebook that:
1. Downloads query species sequences for your specified genomic region
2. Runs BLAST searches against your subject species
3. Generates interactive HTML result files


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
1. Search for *S. cerevisiae* [*ACT1*](https://www.ncbi.nlm.nih.gov/gene/850504) gene on [NCBI](https://www.ncbi.nlm.nih.gov/)

<img src="images/how_to_get_genomic_region.png" alt="How to get genomic region" style="margin-left: 20px;">

2. Find the genomic location: `Chromosome: VI; NC_001138.5 (53260..54696, complement)`


Configure the first cell:
```python
title = "ACT1_synteny" # Prefix for output files from this run

query_sequences_list = [
    {
        'query_species': 's_cerevisiae',           # Species name (must match ASSEMBLY_MAPPING key)
        'protein_sources': ('NP_','XP_'),          # Filter by protein accession prefix
        'show_only_best_matches': 'True',          # 'True', 'False' or 'Both' (two files generated)
        'retrieved_sequences': {
            'download_from_NCBI': True,            # Fetch sequences from NCBI
            'query_chromosome': 'VI',              # Chromosome name
            'start_position': 53260,               # Region start coordinate
            'end_position': 54696,                 # Region end coordinate
            'genes_upstream': 5,                   # Include also 5 genes before the region
            'genes_downstream': 5,                 # Include also 5 genes after the region
        },
    },
]
```
1. Use chromosome `VI` and the corresponding start `53260` and end `54696` coordinates of *ACT1*. 
2. Set upstream/downstream genes to include flanking genes (e.g., 5 each)
> **Note:** The `query_species` value must match the name you used in `ASSEMBLY_MAPPING` (step 3) and your folder name in `1_subject_sequences/`.

### 2. Configure BLAST settings

Choose which BLAST algorithm(s) to use:
- `blastn` - nucleotide vs nucleotide
- `tblastn` - protein vs translated nucleotide
- `tblastx` - translated nucleotide vs translated nucleotide

You can enable multiple types at once - a separate result file will be generated for each:

```python
blast_settings = {
    'blast_type': ['tblastn', 'blastn'],  # Two result files will be generated
    'blast_options': '-outfmt 0 -num_threads 48'
}
```

### 3. Select subject species

Configure which species to search against. Each species can be configured separately:

**Subject Species Parameters:**

| Parameter | Description |
|-----------|-------------|
| `enabled` | `True` to include this species in BLAST search, `False` to skip |
| `maximum_evalue` | E-value threshold - only hits with e-value ≤ this value are kept (e.g., `1e-10`) |
| `minimum_score` | Minimum BLAST bit score - hits below this score are filtered out (0 = no minimum) |
| `additional_blast_parameters` | Extra BLAST command-line options for this species only (e.g., `'-word_size 11'`) |
| `type` | Database type: `'transcriptome'` (search rna.fna) or `'genome'` (search genomic.fna) |

> **Note:** Per-species `maximum_evalue` and `minimum_score` settings override the general values in `blast_options`.

```python
subject_species = {
   's_cerevisiae': {
       'enabled': False,        # Skip searching against query species
       'maximum_evalue': 1e-10,
       'minimum_score': 0,
       'additional_blast_parameters': '',
       'type': 'transcriptome'
   },
   's_pombe': {
       'enabled': True,         # Search this species
       'maximum_evalue': 1e-10,
       'minimum_score': 0,
       'additional_blast_parameters': '',
       'type': 'transcriptome'
   },
   'c_albicans': {
       'enabled': True,         # Search this species
       'maximum_evalue': 1e-10,
       'minimum_score': 0,
       'additional_blast_parameters': '',
       'type': 'transcriptome'
   },
}
```
> **Tip:** Set the query species to `enabled: False` to avoid self-hits. You typically want to search other species, not your query species against itself.

### 4. Map species to [NCBI](https://www.ncbi.nlm.nih.gov/) organism names

Map each species name to its [NCBI](https://www.ncbi.nlm.nih.gov/) organism name (used for Entrez queries and display names in results):

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

## General Features

#### **BLAST Integration**
- **Multiple BLAST algorithms** - Support for BLASTn, tBLASTn, and tBLASTx searches with independent configuration per subject species
- **Automated [NCBI](https://www.ncbi.nlm.nih.gov/) retrieval** - Direct integration with [NCBI](https://www.ncbi.nlm.nih.gov/) E-utilities API for automatic gene sequence downloads from specified genomic regions
- **Custom sequence support** - Incorporate user-provided sequences (e.g., from nanopore sequencing) alongside or instead of [NCBI](https://www.ncbi.nlm.nih.gov/) data
- **Flexible filtering** - Configure E-value thresholds and bit score cutoffs independently for each subject species to account for database size differences

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
- **ID** - Toggles display of [NCBI](https://www.ncbi.nlm.nih.gov/) gene IDs in parentheses next to gene names (e.g., "foxp3 (12345)")
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
- **Gene (query)** - Query species gene names with [NCBI](https://www.ncbi.nlm.nih.gov/) links. Hiding this column removes the source gene identifiers
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

### "HTTP Error 400" from [NCBI](https://www.ncbi.nlm.nih.gov/)
- Reduce the genomic region size or number of upstream/downstream genes
- [NCBI](https://www.ncbi.nlm.nih.gov/) API has limits on query size (~8-10 MB)

### "makeblastdb not found"
- Ensure BLAST+ is installed and in your PATH
- Try running `makeblastdb -version` to verify

### No genes found
- Check that the chromosome format matches [NCBI](https://www.ncbi.nlm.nih.gov/) naming
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
