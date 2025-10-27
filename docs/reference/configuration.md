# Configuration Reference

Complete reference for all BactScout configuration options.

## Configuration File Location

BactScout looks for configuration in this order:

1. File specified with `-c` flag: `pixi run bactscout qc data/ -c /path/to/config.yml`
2. `bactscout_config.yml` in current directory
3. Built-in defaults

## Complete Configuration Example

```yaml
# Database Configuration
bactscout_dbs_path: 'bactscout_dbs'
sylph_db: 'gtdb-r226-c1000-dbv1.syldb'
metrics_file: 'filtered_metrics.csv'
sylph_db_url: 'https://example.com/database.syldb'

# Quality Control Thresholds
coverage_threshold: 30                # Minimum coverage (x-fold)
contamination_threshold: 10           # Maximum contamination (%)
q30_pass_threshold: 0.80              # Minimum Q30% (0.0-1.0)
read_length_pass_threshold: 100       # Minimum read length (bp)

# MLST Species Configuration
mlst_species:
  escherichia_coli: 'Escherichia coli#1'
  salmonella_enterica: 'Salmonella enterica'
  klebsiella_pneumoniae: 'Klebsiella pneumoniae'
  acinetobacter_baumannii: 'Acinetobacter baumannii#1'
  pseudomonas_aeruginosa: 'Pseudomonas aeruginosa'

# System Resources
system_resources:
  cpus: 2
  memory: 4.GB
```

## Configuration Parameters

### Database Settings

#### `bactscout_dbs_path`
- **Type**: string
- **Default**: `'bactscout_dbs'`
- **Description**: Directory path for storing reference databases
- **Example**: `'./databases'` or `'/opt/bactscout_dbs'`

#### `sylph_db`
- **Type**: string
- **Default**: `'gtdb-r226-c1000-dbv1.syldb'`
- **Description**: Filename of Sylph GTDB database
- **Note**: Must exist in `bactscout_dbs_path`

#### `metrics_file`
- **Type**: string
- **Default**: `'filtered_metrics.csv'`
- **Description**: CSV file with species genome metrics (size, GC%)
- **Location**: `{bactscout_dbs_path}/{metrics_file}`

#### `sylph_db_url`
- **Type**: string
- **Default**: `'https://...sylph.syldb'` (built-in)
- **Description**: URL to download Sylph database if not found
- **Note**: Optional, databases auto-download on first run

### Quality Control Thresholds

#### `coverage_threshold`
- **Type**: integer
- **Default**: `30`
- **Range**: 1-1000
- **Unit**: x-fold depth
- **Description**: Minimum required sequencing coverage
- **Impact on PASS/FAIL**: Sample fails if `coverage < threshold`

**Recommendations**:
- `20` - Lenient, exploratory studies
- `30` - Standard, most applications
- `50+` - Strict, critical applications

#### `q30_pass_threshold`
- **Type**: float
- **Default**: `0.80`
- **Range**: 0.0-1.0
- **Unit**: Fraction (0.80 = 80%)
- **Description**: Minimum fraction of bases with Phred quality ≥30
- **Impact on PASS/FAIL**: Sample fails if `q30_percent < threshold`

**Recommendations**:
- `0.70` - Lenient (70% bases Q≥30)
- `0.80` - Standard (80% bases Q≥30)
- `0.90` - Strict (90% bases Q≥30)

#### `read_length_pass_threshold`
- **Type**: integer
- **Default**: `100`
- **Range**: 1-1000
- **Unit**: Base pairs
- **Description**: Minimum average read length
- **Impact on PASS/FAIL**: Sample fails if `mean_read_length < threshold`

**Recommendations**:
- `50` - Short-read platforms with trimming
- `100` - Standard Illumina
- `120+` - Extended reads

#### `contamination_threshold`
- **Type**: float
- **Default**: `10`
- **Range**: 0-100
- **Unit**: Percentage
- **Description**: Maximum allowed contamination from other species
- **Impact on PASS/FAIL**: Sample fails if `contamination_pct > threshold`

**Recommendations**:
- `5` - Strict, pure culture expected
- `10` - Standard, minor contamination acceptable
- `15+` - Lenient, some contamination tolerated

### MLST Species Configuration

#### `mlst_species`
- **Type**: dictionary (key-value pairs)
- **Default**: Includes 5 species
- **Description**: Species with available MLST schemes

**Format**:
```yaml
mlst_species:
  species_key: 'Genus species name'
```

**Key requirements**:
- `species_key`: Used as database directory name (must match `bactscout_dbs/{species_key}/`)
- `value`: Scientific name used for species matching

**Default species**:

```yaml
mlst_species:
  escherichia_coli: 'Escherichia coli#1'
  salmonella_enterica: 'Salmonella enterica'
  klebsiella_pneumoniae: 'Klebsiella pneumoniae'
  acinetobacter_baumannii: 'Acinetobacter baumannii#1'
  pseudomonas_aeruginosa: 'Pseudomonas aeruginosa'
```

**Adding new species**:

1. Prepare MLST database in ARIBA format
2. Place in `bactscout_dbs/{species_key}/`
3. Add to config:
   ```yaml
   mlst_species:
     my_species: 'Genus species'
   ```
4. Update species name in `filtered_metrics.csv` if needed

### System Resources

#### `system_resources.cpus`
- **Type**: integer
- **Default**: `2`
- **Description**: Minimum CPUs required (informational)
- **Note**: Actual thread count controlled by `-t` flag

#### `system_resources.memory`
- **Type**: string
- **Default**: `'4.GB'`
- **Format**: `'{number}.{unit}'` where unit is KB, MB, GB, TB
- **Description**: Minimum RAM required (informational)

## Configuration Use Cases

### Lenient QC (More Samples PASS)

For exploratory studies, low-throughput, or difficult samples:

```yaml
coverage_threshold: 20
q30_pass_threshold: 0.70
read_length_pass_threshold: 80
contamination_threshold: 15
```

### Standard QC (Recommended)

For typical quality control and research:

```yaml
coverage_threshold: 30
q30_pass_threshold: 0.80
read_length_pass_threshold: 100
contamination_threshold: 10
```

### Strict QC (Fewer Samples PASS)

For critical applications requiring high confidence:

```yaml
coverage_threshold: 50
q30_pass_threshold: 0.90
read_length_pass_threshold: 120
contamination_threshold: 5
```

### Diagnostic Lab QC

For clinical/diagnostic samples:

```yaml
coverage_threshold: 100
q30_pass_threshold: 0.90
read_length_pass_threshold: 100
contamination_threshold: 2
```

### Epidemiology Focus

For outbreak investigations prioritizing species ID:

```yaml
coverage_threshold: 20
q30_pass_threshold: 0.75
read_length_pass_threshold: 80
contamination_threshold: 10
mlst_species:
  # Include all relevant species
```

## Using Custom Configurations

### Create and Use Custom Config

```bash
# Create custom config
cp bactscout_config.yml my_lenient_config.yml

# Edit thresholds
nano my_lenient_config.yml

# Use in analysis
pixi run bactscout qc data/ -c my_lenient_config.yml
```

### Per-Batch Configuration

```bash
# Batch 1: Strict QC
pixi run bactscout qc batch1/ -c strict_config.yml -o batch1_results/

# Batch 2: Lenient QC
pixi run bactscout qc batch2/ -c lenient_config.yml -o batch2_results/

# Generate reports with different thresholds
pixi run bactscout summary batch1_results/
pixi run bactscout summary batch2_results/
```

### Override at Command Line

While command-line threshold overrides aren't supported, you can:

1. Create config file with desired values
2. Pass with `-c` flag
3. Or modify the config file before running

## Database Management

### Database Locations

```
bactscout_dbs/
├── gtdb-r226-c1000-dbv1.syldb      # Sylph GTDB database
├── filtered_metrics.csv             # Genome metrics
├── escherichia_coli/                # MLST database
│   └── [ARIBA database files]
├── salmonella_enterica/
│   └── [ARIBA database files]
├── klebsiella_pneumoniae/
│   └── [ARIBA database files]
├── acinetobacter_baumannii/
│   └── [ARIBA database files]
└── pseudomonas_aeruginosa/
    └── [ARIBA database files]
```

### Updating Databases

Update GTDB in config:
```yaml
# Old database
sylph_db: 'gtdb-r226-c1000-dbv1.syldb'

# New database (after downloading)
sylph_db: 'gtdb-r227-c1000-dbv1.syldb'
```

### Custom Reference Database

To use a custom reference database:

1. Create Sylph index from your genomes
2. Place in `bactscout_dbs/`
3. Update config with filename:
   ```yaml
   sylph_db: 'my_custom_ref.syldb'
   ```

## Validation

### Configuration Validation

BactScout validates configuration on startup:

```bash
pixi run bactscout qc data/ -c config.yml
```

**Checked**:
- File exists and is readable
- YAML syntax valid
- Required keys present
- Threshold values in valid ranges
- Database files accessible

**Example error**:
```
Error: Configuration validation failed
  - coverage_threshold must be > 0
  - q30_pass_threshold must be 0.0-1.0
  - Database file not found: gtdb-r226.syldb
```

### Threshold Validation

Values are checked for reasonableness:

| Parameter | Min | Max |
|-----------|-----|-----|
| `coverage_threshold` | 1 | 10000 |
| `q30_pass_threshold` | 0.0 | 1.0 |
| `read_length_pass_threshold` | 1 | 10000 |
| `contamination_threshold` | 0 | 100 |

## Configuration Environment Variables

Set configuration via environment variables:

```bash
export BACTSCOUT_COVERAGE_THRESHOLD=20
export BACTSCOUT_Q30_THRESHOLD=0.75
export BACTSCOUT_CONTAMINATION_THRESHOLD=15

pixi run bactscout qc data/
```

Not yet implemented but planned for future release.

## Example Configurations

### Single-Species MLST Study

```yaml
coverage_threshold: 30
q30_pass_threshold: 0.80
read_length_pass_threshold: 100
contamination_threshold: 5

mlst_species:
  escherichia_coli: 'Escherichia coli#1'
```

### Multi-Species Surveillance

```yaml
coverage_threshold: 20
q30_pass_threshold: 0.75
read_length_pass_threshold: 80
contamination_threshold: 10

mlst_species:
  escherichia_coli: 'Escherichia coli#1'
  salmonella_enterica: 'Salmonella enterica'
  klebsiella_pneumoniae: 'Klebsiella pneumoniae'
  acinetobacter_baumannii: 'Acinetobacter baumannii#1'
  pseudomonas_aeruginosa: 'Pseudomonas aeruginosa'
```

### High-Throughput Screening

```yaml
coverage_threshold: 15
q30_pass_threshold: 0.70
read_length_pass_threshold: 75
contamination_threshold: 20
```

### Clinical Testing

```yaml
coverage_threshold: 100
q30_pass_threshold: 0.95
read_length_pass_threshold: 100
contamination_threshold: 1

system_resources:
  cpus: 8
  memory: 16.GB
```

## Troubleshooting Configuration

### "Configuration file not found"

```bash
# Check if file exists
ls -la bactscout_config.yml

# Use full path
pixi run bactscout qc data/ -c /full/path/to/config.yml
```

### "Invalid YAML syntax"

Check file with YAML validator:
```bash
python -c "import yaml; yaml.safe_load(open('bactscout_config.yml'))"
```

### "Database not found"

Ensure database files exist:
```bash
ls -la bactscout_dbs/

# Should show:
# gtdb-r226-c1000-dbv1.syldb
# filtered_metrics.csv
# [species folders]
```

### "Threshold values ignored"

Thresholds from config file are always used. To override:
1. Create new config file with desired values
2. Pass with `-c` flag

## See Also

- [Configuration Getting Started](../getting-started/configuration.md) - Quick config guide
- [Quality Control Guide](../guide/quality-control.md) - Understanding thresholds
- [Troubleshooting Guide](../guide/troubleshooting.md) - Common issues
