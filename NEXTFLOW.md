# Running BactScout with Nextflow

The repository includes a paired-end Nextflow example in [`nextflow_example/`](nextflow_example/). It runs `bactscout collect` once per sample and then creates a batch summary. The example is configured to use Docker and the `happykhan/bactscout:latest` image; it is a starting point to adapt for your cluster, not a general-purpose production pipeline.

## Requirements

- Nextflow 24.x (the version range used in the Pixi environment).
- Docker, or an adapted workflow and configuration for a container runtime available at your site.
- Paired FASTQ files named `*_R1.fastq.gz` / `*_R2.fastq.gz` or `*_1.fastq.gz` / `*_2.fastq.gz`.
- A BactScout runtime with its reference databases available. The default Sylph GTDB database is approximately 4 GB; MLST databases may also be downloaded during preflight.

The example uses the configuration in `nextflow_example/nextflow.config`. Run it from that directory so Nextflow loads the adjacent configuration:

```bash
cd nextflow_example
nextflow run nextflow.nf \
  --input_dir /path/to/paired-fastqs \
  --output_dir /path/to/results \
  --threads 4
```

The only workflow parameters are `--input_dir`, `--output_dir`, `--config`, `--threads`, and `--help`. The checked-in example defaults to the configuration path inside the published container. If you change the image or run without the container, set `--config` to a config file visible to the process and update the workflow/configuration for your environment.

Outputs include one directory per sample and a top-level `final_summary.csv`. Check Nextflow's work directory and run log for task details. To resume a run, add `-resume` to the same `nextflow run` command.

For direct BactScout batch execution without Nextflow, see the [QC command guide](docs/usage/qc-command.md). For single-sample processing and cluster resource advice, see the [scaling guide](docs/guide/scaling.md).
