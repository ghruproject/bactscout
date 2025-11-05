
# Scaling BactScout for hundreds of samples

This page describes practical ways to run BactScout at scale (tens → hundreds → thousands of samples). It covers two common deployment modes:

- multi-threaded / multi-process runs on a single server (workstation / small node)
- cluster / HPC-style orchestration (job arrays or a workflow engine such as Nextflow)

The core principle is simple: run the per-sample collection/analysis step independently for each sample (the `bactscout collect` command) and then aggregate the per-sample summaries into a single batch summary (the `bactscout summary` command). Running samples independently makes the workflow trivially parallel and fault tolerant.

## Recommended workflow (high level)

1. Prepare an input table or layout of paired reads (R1/R2) and a configuration file (`bactscout_config.yml`).
2. For each sample, run the per-sample subcommand `bactscout collect <R1> <R2> --output <sample_dir> --threads N` so that each sample writes a self-contained output directory (e.g. `<output_dir>/<sample_id>/`).
3. When all per-sample runs have finished (or as they finish), aggregate results by running `bactscout summary <top_level_output_dir> --output final_summary.csv`.

This pattern works the same whether you run samples locally in parallel or dispatch them to an HPC scheduler or workflow engine.

## Local / multi-threaded mode

If you have a machine with many CPU cores and ample RAM, you can process multiple samples in parallel by launching one `bactscout collect` process per sample and constraining threads per-process. Example options:

- Use GNU Parallel or a small Python script to iterate over samples and run `bactscout collect` with `--threads` set to the number of cores you want each sample to consume.
- Keep the sum of `--threads` across concurrent processes less than or equal to the physical cores available. Leave some headroom for OS and I/O.
- If disk I/O is the bottleneck (many compressed reads being read concurrently), reduce the number of concurrent jobs or use faster storage (local NVMe) and stage data to node-local disks.

Example (bash + GNU parallel):

```bash
# samples.tsv: <sample_id>\t<r1.fastq.gz>\t<r2.fastq.gz>
cat samples.tsv | parallel -j 8 \
  'bactscout collect {2} {3} --output results/{1} --threads 4 --config bactscout_config.yml'
```

Notes:

- Use `--threads` to control per-process parallelism. BactScout will pass this to CPU-bound tools it calls.
- Use `--report-resources` (if you want resource usage in the per-sample summary) so you can tune resource allocation later.

## HPC / cluster mode

On an HPC cluster it is common to dispatch one sample per job (or a small group of samples per job). Two popular ways to do this are:

- job arrays (SLURM, SGE): submit many similar jobs that each run `bactscout collect` for one sample
- workflow manager (Nextflow, Snakemake, Cromwell): let the engine discover inputs and schedule processes on cluster nodes

Job-array example (SLURM pseudo-script):

```bash
#SBATCH --array=1-200%40   # run up to 40 tasks concurrently
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=04:00:00

SAMPLE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" samples.tsv | cut -f1)
R1=$(sed -n "${SLURM_ARRAY_TASK_ID}p" samples.tsv | cut -f2)
R2=$(sed -n "${SLURM_ARRAY_TASK_ID}p" samples.tsv | cut -f3)

bactscout collect "$R1" "$R2" --output results/$SAMPLE --threads $SLURM_CPUS_PER_TASK --config bactscout_config.yml
```

Advantages:

- Simple mapping between sample and job; failed samples are easy to retry
- You can size memory/CPU per job based on observed behaviour

Considerations:

- Avoid writing all sample outputs to the same shared directory on some filesystems (e.g., NFS) with very high concurrency. Instead, stage to node-local storage and copy results out.

## Using Nextflow (recommended for production pipelines)

Nextflow is an excellent choice for running BactScout across many samples. The `nextflow_example` directory (see the [github repo](https://github.com/ghruproject/bactscout)) contains a minimal, documented workflow (`nextflow.nf` + `nextflow.config`) that demonstrates:

- automatic discovery of paired-end FASTQ pairs
- per-sample `collect` runs in an isolated process
- publishing per-sample outputs into per-sample directories
- aggregation of per-sample summaries into a single `final_summary.csv`

How the example workflow works (walkthrough):

1. Parameters: the workflow accepts `--input_dir`, `--output_dir`, `--config`, and `--threads`. You can override these at runtime.
2. Input discovery: the workflow builds a channel of tuples `(sample_name, read1, read2)` by matching common naming patterns (`*_R1.fastq.gz`/`*_R2.fastq.gz` or `*_1.fastq.gz`/`*_2.fastq.gz`).
3. `collect_sample` process: for each tuple the workflow runs a containerised `bactscout collect` command. Important features in the example:
   - `stageInMode 'copy'` to safely copy input files to the compute node (reduces shared-FS load)
   - `publishDir "${params.output_dir}/${sample_name}", mode: 'copy'` which ensures each sample's outputs land in a dedicated directory under the main output dir
   - container image is set in the example; set this to your own image or remove container directives if you run on systems without container support
4. `final_summary` process: once per-sample summaries are available, the workflow runs `bactscout summary` to create a single `final_summary.csv` in the top-level output directory.

Why use Nextflow:

- Proven scheduling, retry, and resource isolation across many cluster types (SLURM, PBS, SGE, Kubernetes).
- Automatic staging, container support (Docker/Singularity), and reproducible runs.
- Built-in logging and provenance tracking; easy to resume failed runs.

Practical tips for adapting the example:

- Container image: adjust the `container` entry in `nextflow.nf` to a BactScout image you manage or remove container directives to use the system installation.
- Threads and resource hints: set `params.threads` and configure `process` defaults in `nextflow.config` (cpus, memory). Tune per-sample values to match the tools that BactScout invokes on your inputs.
- Staging and storage: if you're on a shared filesystem, prefer node-local staging (copy) and publish in bulk. If your cluster has a high-performance parallel filesystem, you can choose `stageInMode` accordingly.
- Failure / retry: Nextflow will retry tasks; set sensible `maxRetries` in process config if desired.

### Process details: `collect_sample` and `final_summary`

The `nextflow_example/nextflow.nf` workflow contains two main process blocks that implement the per-sample collection and the final aggregation. Below are the relevant excerpts and a short explanation of each directive so you can adapt them for your site.

1) collect_sample (runs `bactscout collect` for a single sample)

```nextflow
process collect_sample {
  tag { sample_name }
  container 'docker.io/happykhan/bactscout:latest'
  stageInMode 'copy'

  publishDir "${params.output_dir}/${sample_name}", mode: 'copy'
    
  input:
  tuple val(sample_name), path(read1), path(read2)
    
  output:
  path("${sample_name}/${sample_name}_summary.csv"), emit: summary
  path("${sample_name}/**"), emit: all_outputs
    
  script:
  """
  bactscout collect \
    ${read1} \
    ${read2} \
    --output . \
    --threads ${params.threads} \
    --config /app/bactscout_config.yml 2>&1

  """
}
```

Key notes:

- `tag { sample_name }` prints the sample name into Nextflow logs for easy tracing.
- `container` points to an image that contains BactScout and any runtime deps — replace with your image or remove if using system Python.
- `stageInMode 'copy'` copies inputs to the compute node (helps reduce shared-FS contention).
- `publishDir "${params.output_dir}/${sample_name}", mode: 'copy'` ensures each sample's outputs are published into a dedicated directory under your main output dir.
- `input` and `output` declarations define the files passed into and out of the process; `emit` names allow workflow wiring (e.g., summaries collected by the aggregator).

2) final_summary (aggregates per-sample summaries)

```nextflow
process final_summary {
  container 'docker.io/happykhan/bactscout:latest'

  publishDir "${params.output_dir}", mode: 'copy'
    
  input:
  path(summaries)
    
  output:
  path("final_summary.csv")
    
  script:
  """
  bactscout summary \
     . \
    --output .
  """
}
```

Key notes:

- The `final_summary` process collects the per-sample `_summary.csv` files and runs `bactscout summary` to produce a consolidated `final_summary.csv` in the top-level output directory.
- You can tune this process to accept summaries as a channel of files, or pass a glob depending on how you wire the workflow; the example uses `collect_results.summary.collect()` to pass a list of emitted summary paths.

Together these two processes implement the safe, per-sample execution model: independent, containerised per-sample runs that publish self-contained outputs, followed by a small aggregation step that is cheap and easily retryable.

## I/O, storage and filesystem considerations

- Small files: avoid creating millions of tiny files on metadata-limited filesystems. Keep per-sample outputs grouped under a single directory per sample.
- Compression: BactScout reads compressed FASTQs; avoid repeatedly decompressing the same input across many concurrent jobs on a shared filesystem — stage or copy inputs to local disk when possible.
- Temporary directories: prefer node-local scratch (e.g., `$TMPDIR`) for temporary files and then copy the final outputs back to the shared output directory.

## Resource monitoring and tuning

- Start with conservative `--threads` and per-job memory values; collect resource usage (use `--report-resources` when running `bactscout collect`) and tune based on observed CPU and memory footprints.
- Typical per-sample settings depend on the tools BactScout calls (fastp, Sylph, stringMLST). On modest inputs, `--threads 2-4` and 4–8 GB RAM per sample is a reasonable starting point; adjust upwards for larger genomes or deeper coverage.

## Debugging and retries

- Run a single sample locally with verbose logging to confirm the config and container bindings before launching large batches.
- Use the workflow engine's retry behavior or job-array retry logic to re-run failed samples. Keep per-sample output directories intact so you can inspect logs and intermediate files for failures.

## Example: adapt the `nextflow_example` for your site

1. Fork `nextflow_example` (This is in the [github repo](https://github.com/ghruproject/bactscout))and set `params.input_dir` and `params.output_dir` to your paths.
2. Build or choose a container image that bundles BactScout and its runtime dependencies (or install BactScout in the cluster environment and remove the `container` directives).
3. Tune `process` defaults in `nextflow.config` (cpus, memory) and/or set process-level resource hints for `collect_sample`.
4. Test with a small set of samples, confirm `final_summary.csv` contents, then scale to the whole cohort.


BactScout is intentionally designed so each sample is an independent unit of work. That makes it straightforward to scale: choose the orchestration primitive you prefer (parallel processes, job arrays, or a workflow engine), size resources per-sample, stage inputs to local storage when appropriate, and aggregate results with `bactscout summary`.