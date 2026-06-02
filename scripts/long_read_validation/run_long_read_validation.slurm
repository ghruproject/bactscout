#!/usr/bin/env bash
#SBATCH --job-name=bactscout-longread-validation
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=testing/long_read_validation/slurm-%j.out

set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$PWD}"
VALIDATION_DIR="${VALIDATION_DIR:-$ROOT_DIR/testing/long_read_validation}"
GENOME_DIR="$VALIDATION_DIR/genomes"
SIM_DIR="$VALIDATION_DIR/simulated_reads"
OUT_DIR="$VALIDATION_DIR/bactscout_long_output"
DB_DIR="$VALIDATION_DIR/sylph_db"
VALIDATION_CONFIG="$VALIDATION_DIR/bactscout_long_validation.yml"
BADREAD_VENV="${BADREAD_VENV:-$HOME/.venvs/bactscout-badread}"

mkdir -p "$VALIDATION_DIR" "$GENOME_DIR" "$SIM_DIR" "$OUT_DIR" "$DB_DIR"

cd "$ROOT_DIR"

bash scripts/long_read_validation/setup_badread_env.sh
python3 scripts/long_read_validation/download_ncbi_genomes.py "$GENOME_DIR" \
  GCF_000742135.1 GCF_000005845.2

pixi install
pixi run sylph sketch -g "$GENOME_DIR/GCF_000742135.1.fna" "$GENOME_DIR/GCF_000005845.2.fna" -o validation_db -d "$DB_DIR"
mv validation_db.syldb "$DB_DIR/validation_db.syldb"

cat > "$VALIDATION_CONFIG" <<EOF
bactscout_dbs_path: '$DB_DIR'
sylph_db: 'validation_db.syldb'
sylph_db_url: 'unused-for-validation'
metrics_file: '$ROOT_DIR/filtered_metrics.csv'
coverage_warn_threshold: 30
coverage_fail_threshold: 20
contamination_warn_threshold: 10
contamination_fail_threshold: 20
n50_warn: 8000
n50_fail: 4000
platforms:
  ont_r9:
    q_warn: 10
    q_fail: 8
  ont_r10:
    q_warn: 15
    q_fail: 12
  pacbio_hifi:
    q_warn: 20
    q_fail: 18
system_resources:
  cpus: 2
  memory: 4.GB
EOF

pixi run python bactscout.py long preflight --config "$VALIDATION_CONFIG"

GOOD_KP="$SIM_DIR/kleb_good.fastq.gz"
BAD_KP="$SIM_DIR/kleb_bad.fastq.gz"
MIX_90="$SIM_DIR/kleb_ecoli_90_10.fastq.gz"
MIX_80="$SIM_DIR/kleb_ecoli_80_20.fastq.gz"
GOOD_KP_BASE="$SIM_DIR/kleb_good_base.fastq.gz"
BAD_KP_BASE="$SIM_DIR/kleb_bad_base.fastq.gz"
GOOD_ECOLI_BASE="$SIM_DIR/ecoli_good_base.fastq.gz"

"$BADREAD_VENV/bin/badread" simulate \
  --reference "$GENOME_DIR/GCF_000742135.1.fna" \
  --quantity 1x \
  --error_model random \
  --qscore_model ideal \
  --identity 20,3 \
  --length 15000,5000 \
  --glitches 0,0,0 \
  --junk_reads 0 --random_reads 0 --chimeras 0 \
  --start_adapter_seq "" --end_adapter_seq "" \
  | gzip > "$GOOD_KP_BASE"

"$BADREAD_VENV/bin/badread" simulate \
  --reference "$GENOME_DIR/GCF_000742135.1.fna" \
  --quantity 1x \
  --error_model random \
  --qscore_model random \
  --identity 8,2 \
  --length 4000,2000 \
  --glitches 1000,100,100 \
  --junk_reads 5 --random_reads 5 --chimeras 10 \
  --start_adapter_seq "" --end_adapter_seq "" \
  | gzip > "$BAD_KP_BASE"

"$BADREAD_VENV/bin/badread" simulate \
  --reference "$GENOME_DIR/GCF_000005845.2.fna" \
  --quantity 1x \
  --error_model random \
  --qscore_model ideal \
  --identity 18,3 \
  --length 15000,5000 \
  --glitches 0,0,0 \
  --junk_reads 0 --random_reads 0 --chimeras 0 \
  --start_adapter_seq "" --end_adapter_seq "" \
  | gzip > "$GOOD_ECOLI_BASE"

{ for _i in $(seq 1 35); do cat "$GOOD_KP_BASE"; done; } > "$GOOD_KP"
{ for _i in $(seq 1 35); do cat "$BAD_KP_BASE"; done; } > "$BAD_KP"
{ for _i in $(seq 1 36); do cat "$GOOD_KP_BASE"; done; for _i in $(seq 1 4); do cat "$GOOD_ECOLI_BASE"; done; } > "$MIX_90"
{ for _i in $(seq 1 32); do cat "$GOOD_KP_BASE"; done; for _i in $(seq 1 8); do cat "$GOOD_ECOLI_BASE"; done; } > "$MIX_80"

pixi run python bactscout.py long collect "$GOOD_KP" --platform ont_r10 --output "$OUT_DIR" --threads 4 --config "$VALIDATION_CONFIG" --skip-preflight
pixi run python bactscout.py long collect "$BAD_KP" --platform ont_r10 --output "$OUT_DIR" --threads 4 --config "$VALIDATION_CONFIG" --skip-preflight
pixi run python bactscout.py long collect "$MIX_90" --platform ont_r10 --output "$OUT_DIR" --threads 4 --config "$VALIDATION_CONFIG" --skip-preflight
pixi run python bactscout.py long collect "$MIX_80" --platform ont_r10 --output "$OUT_DIR" --threads 4 --config "$VALIDATION_CONFIG" --skip-preflight

pixi run python bactscout.py long summary "$OUT_DIR" --output "$OUT_DIR"

echo "Validation outputs written to $OUT_DIR"