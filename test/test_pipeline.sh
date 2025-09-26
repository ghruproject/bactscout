#!/bin/bash
#
# Test script for GHRU ReadQC Pipeline
# This script performs basic validation and testing of the pipeline components
#

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

print_info "Testing GHRU ReadQC Pipeline"
print_info "Project directory: $PROJECT_DIR"

# Test 1: Check if all required files exist
print_info "Test 1: Checking required files..."

REQUIRED_FILES=(
    "main.nf"
    "nextflow.config"
    "environment.yml"
    "bin/pick_smallest_genome.py"
    "bin/calculate_depth.py"
    "run_pipeline.sh"
)

ALL_FILES_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$PROJECT_DIR/$file" ]]; then
        print_success "Found: $file"
    else
        print_error "Missing: $file"
        ALL_FILES_EXIST=false
    fi
done

if [[ "$ALL_FILES_EXIST" == "true" ]]; then
    print_success "All required files present"
else
    print_error "Some required files are missing"
    exit 1
fi

# Test 2: Check if scripts are executable
print_info "Test 2: Checking script permissions..."

EXECUTABLE_FILES=(
    "bin/pick_smallest_genome.py"
    "bin/calculate_depth.py"
    "run_pipeline.sh"
    "test/generate_test_data.py"
)

for file in "${EXECUTABLE_FILES[@]}"; do
    if [[ -x "$PROJECT_DIR/$file" ]]; then
        print_success "Executable: $file"
    else
        print_warning "Not executable: $file"
        chmod +x "$PROJECT_DIR/$file"
        print_info "Made executable: $file"
    fi
done

# Test 3: Validate Python scripts syntax
print_info "Test 3: Validating Python scripts..."

PYTHON_SCRIPTS=(
    "bin/pick_smallest_genome.py"
    "bin/calculate_depth.py"
    "test/generate_test_data.py"
)

for script in "${PYTHON_SCRIPTS[@]}"; do
    if python3 -m py_compile "$PROJECT_DIR/$script"; then
        print_success "Python syntax valid: $script"
    else
        print_error "Python syntax error: $script"
        exit 1
    fi
done

# Test 4: Test helper scripts with --help
print_info "Test 4: Testing helper scripts..."

cd "$PROJECT_DIR"

if python3 bin/pick_smallest_genome.py --help > /dev/null 2>&1; then
    print_success "pick_smallest_genome.py help works"
else
    print_error "pick_smallest_genome.py help failed"
fi

if python3 bin/calculate_depth.py --help > /dev/null 2>&1; then
    print_success "calculate_depth.py help works"
else
    print_error "calculate_depth.py help failed"
fi

if python3 test/generate_test_data.py --help > /dev/null 2>&1; then
    print_success "generate_test_data.py help works"
else
    print_error "generate_test_data.py help failed"
fi

# Test 5: Generate small test dataset
print_info "Test 5: Generating test data..."

cd "$PROJECT_DIR"
if python3 test/generate_test_data.py --num_samples 1 --num_reads 1000 --output_dir test/data; then
    print_success "Test data generation successful"
    
    # Check if files were created
    if [[ -f "test/data/test_sample_01_R1.fastq.gz" ]] && [[ -f "test/data/test_sample_01_R2.fastq.gz" ]]; then
        print_success "Test FASTQ files created"
    else
        print_error "Test FASTQ files not found"
    fi
else
    print_error "Test data generation failed"
fi

# Test 6: Check Nextflow syntax (if Nextflow is available)
print_info "Test 6: Checking Nextflow availability..."

if command -v nextflow &> /dev/null; then
    print_success "Nextflow found"
    
    # Try to validate the pipeline syntax
    if nextflow run main.nf --help > /dev/null 2>&1; then
        print_success "Nextflow pipeline syntax is valid"
    else
        print_warning "Nextflow pipeline syntax validation failed or help not working as expected"
    fi
else
    print_warning "Nextflow not found - install Nextflow to validate pipeline syntax"
    print_info "Installation: curl -s https://get.nextflow.io | bash"
fi

# Test 7: Check conda environment specification
print_info "Test 7: Validating conda environment..."

if conda env create --dry-run -f environment.yml > /dev/null 2>&1; then
    print_success "Conda environment specification is valid"
elif command -v conda &> /dev/null; then
    print_warning "Conda environment validation failed - some packages may not be available"
else
    print_warning "Conda not found - cannot validate environment"
fi

print_info "Pipeline testing completed!"
print_info ""
print_info "Next steps:"
print_info "1. Install Nextflow: curl -s https://get.nextflow.io | bash"
print_info "2. Install conda environment: conda env create -f environment.yml"
print_info "3. Run test: ./run_pipeline.sh -i test/data -o test/results"