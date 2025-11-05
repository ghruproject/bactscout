# Configuration

BactScout uses a YAML configuration file to define analysis parameters and thresholds.

## Default Configuration

The default `bactscout_config.yml` (project root) is the single source of truth for
thresholds, database locations, and system requirements. Below is the current
configuration shipped with this repository:

```yaml
bactscout_dbs_path: 'bactscout_dbs'
sylph_db: 'gtdb-r226-c1000-dbv1.syldb'
metrics_file: 'filtered_metrics.csv'
sylph_db_url: 'http://faust.compbio.cs.cmu.edu/sylph-stuff/gtdb-r226-c1000-dbv1.syldb'

# QC Thresholds - Support both WARN and FAIL levels
# Coverage thresholds (in x)
coverage_warn_threshold: 30
coverage_fail_threshold: 20

# Contamination thresholds (% of top species, lower is more contaminated)
contamination_warn_threshold: 5
contamination_fail_threshold: 10

# Q30 thresholds (fraction of bases >= Q30)
q30_warn_threshold: 0.80
q30_fail_threshold: 0.70

# Read length thresholds (mean read length in bp)
read_length_warn_threshold: 80
read_length_fail_threshold: 100

# Duplication rate thresholds (fraction of duplicate reads)
duplication_warn_threshold: 0.20
duplication_fail_threshold: 0.30

# GC content failure threshold (% of reads with unexpected GC content)
gc_fail_percentage: 5

# N-content threshold (fraction of reads with too many N's)
n_content_threshold: 0.001
# Adapter overrepresented sequences threshold (number of overrepresented sequences)
adapter_overrep_threshold: 5

mlst_species:
  escherichia_coli: 'Escherichia coli#1'
  salmonella_enterica: 'Salmonella enterica'
  klebsiella_pneumoniae: 'Klebsiella pneumoniae'
  acinetobacter_baumannii: 'Acinetobacter baumannii#1'
  pseudomonas_aeruginosa: 'Pseudomonas aeruginosa'
system_resources:
  cpus: 2
  memory: 4.GB
```

## Custom Configuration

Create a custom config and pass it to BactScout:

```bash
cp bactscout_config.yml my_config.yml
# Edit my_config.yml as needed
pixi run bactscout qc data/ -c my_config.yml
```

## Configuration Parameters

### Database Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `bactscout_dbs_path` | `bactscout_dbs` | Directory for storing reference databases |
| `sylph_db` | `gtdb-r226-c1000-dbv1.syldb` | Sylph GTDB database filename |
| `metrics_file` | `filtered_metrics.csv` | Species-specific genome size and GC content metrics |
| `sylph_db_url` | [See config] | URL to download Sylph database if not found |

### Using alternative Sylph databases

Sylph provides a set of pre-built reference databases targeting different trade-offs of sensitivity, specificity and runtime (see [the Sylph pre-built databases page](https://sylph-docs.github.io/pre%E2%80%90built-databases/).

- The default database shipped in BactScout (`gtdb-r226-c1000-dbv1.syldb`) is compact and fast, and works well for many routine surveillance tasks, but it may be smaller than the largest available references and therefore slightly less sensitive for rare or unusual species.
- Larger, more comprehensive Sylph databases (for example full GTDB builds or RefSeq-style databases) include many more taxa and yield higher sensitivity at the cost of increased disk usage, higher memory requirements, and longer profiling runtimes.

If you want to use an alternative Sylph database, update these fields in `bactscout_config.yml`:

```yaml
sylph_db: 'my-large-db.syldb'
sylph_db_url: 'https://example.org/path/to/my-large-db.syldb'
bactscout_dbs_path: '/path/to/local/dbs'
```

Notes and recommendations:

- You can point `sylph_db_url` at any HTTP(S)-accessible `.syldb` file; the `preflight` command will try to download it into `bactscout_dbs_path` when missing.
- Expect larger `.syldb` files to require more disk space (tens to hundreds of GB for very large RefSeq/GTDB builds) and more RAM during profiling. Test on a small subset first to measure performance impact.
- If you are running BactScout inside containers, ensure the database path is mounted into the container and that permissions allow the process to read the file.
- If you need the highest sensitivity for taxonomic assignment, pick one of the larger pre-built databases from the Sylph docs, but accept that profiling will take longer.

Example: switch to a larger GTDB build (pseudo-URL):

```yaml
sylph_db: 'gtdb-r226-full.syldb'
sylph_db_url: 'https://sylph-docs.github.io/pre-built-databases/gtdb-r226-full.syldb'
```

Use the `pixi run bactscout preflight` command after updating the config to validate the database download and ensure tool availability.

### Quality Control Thresholds

Many thresholds are expressed as WARN/FAIL pairs; tests and the CLI use these
separately to produce PASS/WARNING/FAIL decisions.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `coverage_warn_threshold` | 30 | Coverage (×) above which samples are considered OK (warning threshold) |
| `coverage_fail_threshold` | 20 | Coverage (×) below which samples are considered FAIL |
| `contamination_warn_threshold` | 5 | Contamination (%) warning threshold (percent of reads not from dominant species) |
| `contamination_fail_threshold` | 10 | Contamination (%) fail threshold |
| `q30_warn_threshold` | 0.80 | Fraction of bases with Q ≥ 30 for WARN |
| `q30_fail_threshold` | 0.70 | Fraction of bases with Q ≥ 30 for FAIL |
| `read_length_warn_threshold` | 80 | Mean read length (bp) WARN threshold |
| `read_length_fail_threshold` | 100 | Mean read length (bp) FAIL threshold |
| `duplication_warn_threshold` | 0.20 | Fraction duplicate reads WARN |
| `duplication_fail_threshold` | 0.30 | Fraction duplicate reads FAIL |
| `gc_fail_percentage` | 5 | The GC ranges are determined via [Qualibact](https://happykhan.github.io/qualibact/) for a known species. These values are used to WARN. This option controlls the adjustment to the cutoff percent with unexpected GC content that triggers FAIL |
| `n_content_threshold` | 0.001 | Fraction of reads with too many N's that triggers FAIL |
| `adapter_overrep_threshold` | 5 | Number of overrepresented adapters before warning/failing |


### Other QC applied (auto-determined)

In addition to the thresholds above, BactScout applies several QC checks that are
automatically determined from species assignment and the metrics database:

- **Genome size** — obtained from the `metrics_file` (QualiBact-derived values) and the predicted species from Sylph; used to compute an estimated coverage when Sylph-derived coverage is unavailable.
- **GC ranges** — species-specific GC lower/upper bounds are read from the QualiBact-derived metrics file. A sample GC within the species bounds is considered PASS; values slightly outside the bounds trigger a WARNING; values outside the bounds plus the configured `gc_fail_percentage` buffer are flagged as FAIL.

These values are inferred at runtime (species + metrics) and do not require manual setting in the config.


### MLST Species

Define species with available MLST schemes:

```yaml
mlst_species:
  escherichia_coli: 'Escherichia coli#1'      # Species directory: escherichia_coli
  salmonella_enterica: 'Salmonella enterica'   # Species directory: salmonella_enterica
```

The **key** is used as the database directory name, the **value** is the scientific name for species matching.

For a complete list of PUBMLST-format names supported by BactScout, see the
dedicated page and raw list included with the docs:

- [Human-readable list](./mlst-species.md)
- [Raw machine-readable copy](./mlst_species.txt)

Use the exact PUBMLST-format key as the directory name under
`bactscout_dbs/` when adding MLST databases.

To add MLST support for a new species:
1. Prepare MLST databases following [PUBMLST format](mlst-species.md)
2. Add to config:
   ```yaml
   mlst_species:
     my_species: 'Genus species'
   ```
3. Place databases in `bactscout_dbs/my_species/`
4. Run BactScout normally

### System Resources

```yaml
system_resources:
  cpus: 2              # Minimum CPUs required
  memory: 4.GB         # Minimum memory required
```

## Adjusting Thresholds

Example: Lower coverage threshold for low-depth studies

```yaml
coverage_threshold: 20  # Instead of 30x
q30_pass_threshold: 0.75  # Instead of 0.80 (75% instead of 80%)
read_length_pass_threshold: 80  # Instead of 100 bp
```


!!! tip "Need Help?"
    See [Troubleshooting](../guide/troubleshooting.md) for help with configuration issues.
