#!/usr/bin/env python3
"""
Generate synthetic test FASTQ data for the GHRU ReadQC pipeline.
This script creates small paired-end FASTQ files for testing purposes.
"""

import argparse
import gzip
import random
import os
from pathlib import Path

def generate_sequence(length, gc_content=0.5):
    """Generate a random DNA sequence with specified GC content."""
    bases = ['A', 'T', 'G', 'C']
    gc_bases = ['G', 'C']
    at_bases = ['A', 'T']
    
    sequence = []
    for _ in range(length):
        if random.random() < gc_content:
            sequence.append(random.choice(gc_bases))
        else:
            sequence.append(random.choice(at_bases))
    
    return ''.join(sequence)

def generate_quality_string(length, min_quality=20, max_quality=40):
    """Generate a quality string with random quality scores."""
    qualities = []
    for _ in range(length):
        # Quality score in Phred+33 format
        quality = random.randint(min_quality, max_quality)
        qualities.append(chr(quality + 33))
    return ''.join(qualities)

def add_sequencing_errors(sequence, error_rate=0.01):
    """Add random sequencing errors to a sequence."""
    bases = ['A', 'T', 'G', 'C']
    sequence_list = list(sequence)
    
    for i in range(len(sequence_list)):
        if random.random() < error_rate:
            # Replace with a different base
            original_base = sequence_list[i]
            possible_bases = [b for b in bases if b != original_base]
            sequence_list[i] = random.choice(possible_bases)
    
    return ''.join(sequence_list)

def generate_paired_reads(num_reads, read_length, insert_size, insert_sd):
    """Generate paired-end reads from synthetic sequences."""
    reads_r1 = []
    reads_r2 = []
    
    for i in range(num_reads):
        # Generate fragment
        fragment_length = max(read_length * 2, int(random.gauss(insert_size, insert_sd)))
        fragment = generate_sequence(fragment_length)
        
        # Extract R1 and R2
        r1_seq = fragment[:read_length]
        r2_seq = fragment[-read_length:][::-1]  # Reverse complement
        r2_seq = r2_seq.translate(str.maketrans('ATGC', 'TACG'))
        
        # Add sequencing errors
        r1_seq = add_sequencing_errors(r1_seq)
        r2_seq = add_sequencing_errors(r2_seq)
        
        # Generate quality scores
        r1_qual = generate_quality_string(len(r1_seq))
        r2_qual = generate_quality_string(len(r2_seq))
        
        # Create FASTQ entries
        read_id = f"@read_{i+1:06d}"
        r1_entry = f"{read_id}/1\n{r1_seq}\n+\n{r1_qual}\n"
        r2_entry = f"{read_id}/2\n{r2_seq}\n+\n{r2_qual}\n"
        
        reads_r1.append(r1_entry)
        reads_r2.append(r2_entry)
    
    return reads_r1, reads_r2

def write_fastq_file(reads, filename, compress=True):
    """Write reads to a FASTQ file."""
    if compress:
        with gzip.open(filename, 'wt') as f:
            f.writelines(reads)
    else:
        with open(filename, 'w') as f:
            f.writelines(reads)

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic test FASTQ data")
    parser.add_argument('--output_dir', '-o', default='./test/data', 
                       help='Output directory for test files')
    parser.add_argument('--num_samples', '-n', type=int, default=2,
                       help='Number of samples to generate')
    parser.add_argument('--num_reads', type=int, default=10000,
                       help='Number of reads per sample')
    parser.add_argument('--read_length', type=int, default=150,
                       help='Read length in base pairs')
    parser.add_argument('--insert_size', type=int, default=300,
                       help='Mean insert size')
    parser.add_argument('--insert_sd', type=int, default=50,
                       help='Insert size standard deviation')
    parser.add_argument('--compress', action='store_true', default=True,
                       help='Compress output files with gzip')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {args.num_samples} test samples in {output_dir}")
    print(f"Parameters: {args.num_reads} reads, {args.read_length} bp read length")
    
    for sample_num in range(1, args.num_samples + 1):
        sample_name = f"test_sample_{sample_num:02d}"
        print(f"Generating sample: {sample_name}")
        
        # Generate paired reads
        reads_r1, reads_r2 = generate_paired_reads(
            args.num_reads, args.read_length, args.insert_size, args.insert_sd
        )
        
        # Determine file extension
        ext = '.fastq.gz' if args.compress else '.fastq'
        
        # Write files
        r1_file = output_dir / f"{sample_name}_R1{ext}"
        r2_file = output_dir / f"{sample_name}_R2{ext}"
        
        write_fastq_file(reads_r1, r1_file, args.compress)
        write_fastq_file(reads_r2, r2_file, args.compress)
        
        print(f"  Created: {r1_file}")
        print(f"  Created: {r2_file}")
    
    print(f"\nTest data generation complete!")
    print(f"Files created in: {output_dir}")
    
    # Create a simple README for test data
    readme_path = output_dir / "README.txt"
    with open(readme_path, 'w') as f:
        f.write("Synthetic Test Data for GHRU ReadQC Pipeline\n")
        f.write("=" * 45 + "\n\n")
        f.write(f"Generated {args.num_samples} samples with:\n")
        f.write(f"- {args.num_reads:,} reads per sample\n")
        f.write(f"- {args.read_length} bp read length\n")
        f.write(f"- {args.insert_size} ± {args.insert_sd} bp insert size\n")
        f.write(f"- Random DNA sequences with ~50% GC content\n")
        f.write(f"- ~1% sequencing error rate\n\n")
        f.write("These files are suitable for testing the pipeline functionality\n")
        f.write("but do not represent real biological data.\n")
    
    print(f"Documentation: {readme_path}")

if __name__ == "__main__":
    main()