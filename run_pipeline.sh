#!/bin/bash
#
# GHRU ReadQC Pipeline Runner Script
# 
# This script provides a convenient way to run the GHRU ReadQC pipeline
# with common configurations and error checking.
#

set -euo pipefail

# Default parameters
INPUT_DIR=""
OUTPUT_DIR="./results"
PROFILE="conda"
RESUME=false
HELP=false

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help message
show_help() {
    cat << EOF
GHRU ReadQC Pipeline Runner

Usage: $0 [OPTIONS]

Required:
    -i, --input DIR         Input directory containing paired FASTQ files

Optional:
    -o, --output DIR        Output directory (default: ./results)
    -p, --profile PROFILE   Execution profile: conda, docker, singularity (default: conda)
    -r, --resume            Resume previous run
    -h, --help              Show this help message

Examples:
    # Basic run with conda
    $0 -i /path/to/fastq/files -o /path/to/results

    # Run with docker profile
    $0 -i /path/to/fastq/files -o /path/to/results -p docker

    # Resume a previous run
    $0 -i /path/to/fastq/files -o /path/to/results -r

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input)
            INPUT_DIR="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -r|--resume)
            RESUME=true
            shift
            ;;
        -h|--help)
            HELP=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Show help if requested
if [[ "$HELP" == "true" ]]; then
    show_help
    exit 0
fi

# Validate required parameters
if [[ -z "$INPUT_DIR" ]]; then
    print_error "Input directory is required (-i/--input)"
    show_help
    exit 1
fi

# Check if input directory exists
if [[ ! -d "$INPUT_DIR" ]]; then
    print_error "Input directory does not exist: $INPUT_DIR"
    exit 1
fi

# Check for FASTQ files in input directory
FASTQ_COUNT=$(find "$INPUT_DIR" -name "*.fastq.gz" -o -name "*.fq.gz" -o -name "*.fastq" -o -name "*.fq" | wc -l)
if [[ $FASTQ_COUNT -eq 0 ]]; then
    print_error "No FASTQ files found in input directory: $INPUT_DIR"
    print_info "Expected file patterns: *.fastq.gz, *.fq.gz, *.fastq, *.fq"
    exit 1
fi

print_info "Found $FASTQ_COUNT FASTQ files in input directory"

# Check if Nextflow is available
if ! command -v nextflow &> /dev/null; then
    print_error "Nextflow is not installed or not in PATH"
    print_info "Please install Nextflow: https://nextflow.io/docs/latest/getstarted.html"
    exit 1
fi

# Print configuration
print_info "Pipeline Configuration:"
print_info "  Input directory: $INPUT_DIR"
print_info "  Output directory: $OUTPUT_DIR"
print_info "  Profile: $PROFILE"
print_info "  Resume: $RESUME"

# Build Nextflow command
NEXTFLOW_CMD="nextflow run main.nf"
NEXTFLOW_CMD="$NEXTFLOW_CMD --input '$INPUT_DIR'"
NEXTFLOW_CMD="$NEXTFLOW_CMD --outdir '$OUTPUT_DIR'"
NEXTFLOW_CMD="$NEXTFLOW_CMD -profile $PROFILE"

if [[ "$RESUME" == "true" ]]; then
    NEXTFLOW_CMD="$NEXTFLOW_CMD -resume"
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

print_info "Starting pipeline execution..."
print_info "Command: $NEXTFLOW_CMD"

# Execute the pipeline
eval $NEXTFLOW_CMD

# Check if pipeline completed successfully
if [[ $? -eq 0 ]]; then
    print_success "Pipeline completed successfully!"
    print_info "Results are available in: $OUTPUT_DIR"
    
    # Check for MultiQC report
    MULTIQC_REPORT="$OUTPUT_DIR/multiqc/multiqc_report.html"
    if [[ -f "$MULTIQC_REPORT" ]]; then
        print_success "MultiQC report generated: $MULTIQC_REPORT"
    fi
else
    print_error "Pipeline failed!"
    print_info "Check the Nextflow log (.nextflow.log) for details"
    exit 1
fi