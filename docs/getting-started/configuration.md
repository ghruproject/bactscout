# Configuration

BactScout uses a YAML configuration file to define analysis parameters and thresholds.

## Default Configuration

The default `bactscout_config.yml` is located in the project root:

```yaml
bactscout_dbs_path: 'bactscout_dbs'
sylph_db: 'gtdb-r226-c1000-dbv1.syldb'
metrics_file: 'filtered_metrics.csv'
coverage_threshold: 30
contamination_threshold: 10
q30_pass_threshold: 0.80
read_length_pass_threshold: 100
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

## Configuration Parameters

### Database Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `bactscout_dbs_path` | `bactscout_dbs` | Directory for storing reference databases |
| `sylph_db` | `gtdb-r226-c1000-dbv1.syldb` | Sylph GTDB database filename |
| `metrics_file` | `filtered_metrics.csv` | Species-specific genome size and GC content metrics |
| `sylph_db_url` | [See config] | URL to download Sylph database if not found |

### Quality Control Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `coverage_threshold` | 30 | Minimum coverage depth (in reads/base) |
| `contamination_threshold` | 10 | Maximum % of reads from other species |
| `q30_pass_threshold` | 0.80 | Minimum percentage of bases with Q≥30 |
| `read_length_pass_threshold` | 100 | Minimum mean read length (bp) |

### MLST Species

Define species with available MLST schemes:

```yaml
mlst_species:
  escherichia_coli: 'Escherichia coli#1'      # Species directory: escherichia_coli
  salmonella_enterica: 'Salmonella enterica'   # Species directory: salmonella_enterica
```

The **key** is used as the database directory name, the **value** is the scientific name for species matching.

### System Resources

```yaml
system_resources:
  cpus: 2              # Minimum CPUs required
  memory: 4.GB         # Minimum memory required
```

## Custom Configuration

Create a custom config and pass it to BactScout:

```bash
pixi run bactscout qc data/ -c my_config.yml
```

## Adjusting Thresholds

Example: Lower coverage threshold for low-depth studies

```yaml
coverage_threshold: 20  # Instead of 30x
q30_pass_threshold: 0.75  # Instead of 0.80 (75% instead of 80%)
read_length_pass_threshold: 80  # Instead of 100 bp
```

## Adding New Species

To add MLST support for a new species:

1. Prepare MLST databases following [ARIBA format](https://ariba.readthedocs.io/)
2. Add to config:
   ```yaml
   mlst_species:
     my_species: 'Genus species'
   ```
3. Place databases in `bactscout_dbs/my_species/`
4. Run BactScout normally

!!! tip "Need Help?"
    See [Troubleshooting](../guide/troubleshooting.md) for help with configuration issues.
