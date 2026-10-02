# Configuration reference

BactScout ships separate YAML files for short-read and long-read workflows:

- Short reads: `bactscout/config/bactscout_config.yml`
- Long reads: `bactscout/config/bactscout_long_config.yml`

Use `--config` (`-c`) to select a copy or an alternate file. Use `--database` to select where external Sylph and MLST databases are stored. These are the configuration options exposed by the current CLI; it does not provide per-threshold command-line or environment-variable overrides.

```bash
pixi run bactscout qc reads/ --config short.yml --database /data/bactscout-db
pixi run bactscout long qc long_reads/ --platform ont_r10 \
  --config long.yml --database /data/bactscout-db
```

## Short-read settings

The following table lists the values in the checked-in default short-read configuration. For the QC decision rules and output fields, see the [quality-control guide](../guide/quality-control.md) and [output-format reference](../usage/output-format.md).

| Key | Default | Purpose |
|---|---:|---|
| `sylph_db` | `gtdb-r226-c1000-dbv1.syldb` | Sylph database filename |
| `sylph_db_url` | Configured Sylph download URL | URL used when that file is missing |
| `coverage_warn_threshold` | `30` | Coverage decision cutoff |
| `coverage_fail_threshold` | `20` | Coverage decision cutoff |
| `contamination_warn_threshold` | `10` | Secondary-species abundance cutoff (%) |
| `contamination_fail_threshold` | `20` | Secondary-species abundance cutoff (%) |
| `q30_warn_threshold` | `0.80` | Q30 fraction cutoff |
| `q30_fail_threshold` | `0.70` | Q30 fraction cutoff |
| `read_length_warn_threshold` | `80` | Mean read length cutoff (bp) |
| `read_length_fail_threshold` | `100` | Mean read length cutoff (bp) |
| `duplication_warn_threshold` | `0.20` | Duplicate-read fraction cutoff |
| `duplication_fail_threshold` | `0.30` | Duplicate-read fraction cutoff |
| `gc_fail_percentage` | `5` | Tolerance used with species GC bounds (%) |
| `n_content_threshold` | `0.001` | N-content fraction cutoff |
| `adapter_overrep_threshold` | `5` | Overrepresented adapter count cutoff |

`mlst_species` maps a database directory key to the species name passed to StringMLST. The default file lists *Escherichia coli*, *Salmonella enterica*, *Klebsiella pneumoniae*, *Acinetobacter baumannii*, and *Pseudomonas aeruginosa*. For database files and adding a scheme, see the [MLST species guide](../getting-started/mlst-species.md).

`metrics_file` may be set to a CSV with species genome-size and GC metrics. By default, BactScout uses its bundled `bactscout/config/filtered_metrics.csv`. `system_resources.cpus` and `system_resources.memory` describe the configured resource requirements checked by preflight; runtime threads are selected with `--threads`.

The older single-cutoff keys `coverage_threshold` and `contamination_threshold` remain as compatibility fallbacks when their two named cutoffs are absent. New configurations should copy the shipped two-cutoff keys. Other historical names such as `q30_pass_threshold` and `read_length_pass_threshold` are not current settings.

## Long-read settings

The default long-read file has its own coverage, contamination, N50, and platform quality settings:

| Key | Default | Purpose |
|---|---:|---|
| `sylph_db`, `sylph_db_url` | Same default database as short reads | Sylph reference database and download URL |
| `coverage_warn_threshold` | `30` | Coverage decision cutoff |
| `coverage_fail_threshold` | `20` | Coverage decision cutoff |
| `contamination_warn_threshold` | `10` | Secondary-species abundance cutoff (%) |
| `contamination_fail_threshold` | `20` | Secondary-species abundance cutoff (%) |
| `n50_warn` | `8000` | Read N50 cutoff (bp) |
| `n50_fail` | `4000` | Read N50 cutoff (bp) |

`platforms` defines `q_warn` and `q_fail` values for `ont_r9`, `ont_r10`, and `pacbio_hifi`. The selected key is required with `--platform`; see the [long-read QC guide](../usage/long-read-qc.md). `system_resources` has the same meaning as in the short-read config.

## Database storage

The database directory is selected automatically unless `--database` or `bactscout_dbs_path` in the configuration supplies a location. Pixi/source checkouts use `bactscout_dbs/` when it exists; otherwise the platform's user-data location is used. Sylph downloads on preflight if missing. The default Sylph database is approximately 4 GB; StringMLST scheme files add to the storage requirement.

An example database directory contains the Sylph index and one subdirectory per configured MLST scheme:

```text
bactscout_dbs/
├── gtdb-r226-c1000-dbv1.syldb
├── escherichia_coli/
├── salmonella_enterica/
├── klebsiella_pneumoniae/
├── acinetobacter_baumannii/
└── pseudomonas_aeruginosa/
```

The species metrics CSV is bundled with BactScout under `bactscout/config/`; it is not part of `bactscout_dbs/`.

## Editing a configuration

Copy the relevant default file, keep the supported key names, edit the values, and pass the copy with `--config`. A QC run reads thresholds when it processes samples. The `summary` command only combines per-sample summaries; it does not re-evaluate results with a new configuration.
