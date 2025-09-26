#!/usr/bin/env python3
"""
Helper script to calculate read depth using the selected genome size.
This script estimates sequencing depth by counting reads and dividing by genome size.
"""

import argparse
import gzip
import sys
import logging
from pathlib import Path

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def count_reads_and_bases(fastq_file):
    """
    Count the number of reads and total bases in a FASTQ file.
    
    Args:
        fastq_file (str): Path to FASTQ file (can be gzipped)
        
    Returns:
        tuple: (read_count, total_bases, avg_read_length)
    """
    logger = logging.getLogger(__name__)
    
    read_count = 0
    total_bases = 0
    
    try:
        # Determine if file is gzipped
        if fastq_file.endswith('.gz'):
            file_handle = gzip.open(fastq_file, 'rt')
        else:
            file_handle = open(fastq_file, 'r')
        
        with file_handle as f:
            line_count = 0
            for line in f:
                line_count += 1
                if line_count % 4 == 2:  # Sequence line in FASTQ format
                    sequence = line.strip()
                    total_bases += len(sequence)
                    read_count += 1
                    
                    # Progress reporting for large files
                    if read_count % 100000 == 0:
                        logger.debug(f"Processed {read_count:,} reads from {Path(fastq_file).name}")
        
        avg_read_length = total_bases / read_count if read_count > 0 else 0
        logger.info(f"File {Path(fastq_file).name}: {read_count:,} reads, {total_bases:,} bases, avg length {avg_read_length:.1f}")
        
        return read_count, total_bases, avg_read_length
        
    except Exception as e:
        logger.error(f"Error reading {fastq_file}: {e}")
        return 0, 0, 0

def parse_genome_info(genome_info_file):
    """
    Parse the genome information file created by pick_smallest_genome.py.
    
    Args:
        genome_info_file (str): Path to genome info file
        
    Returns:
        dict: Genome information including size
    """
    logger = logging.getLogger(__name__)
    
    genome_info = {}
    
    try:
        with open(genome_info_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '\t' in line:
                    key, value = line.split('\t', 1)
                    genome_info[key] = value
        
        # Convert genome size to integer
        if 'estimated_genome_size' in genome_info:
            genome_info['estimated_genome_size'] = int(genome_info['estimated_genome_size'])
            logger.info(f"Parsed genome size: {genome_info['estimated_genome_size']:,} bp")
        else:
            logger.error("No genome size found in genome info file")
            return None
            
        return genome_info
        
    except Exception as e:
        logger.error(f"Error parsing genome info file: {e}")
        return None

def calculate_depth(read_files, genome_size):
    """
    Calculate sequencing depth from read files and genome size.
    
    Args:
        read_files (list): List of FASTQ file paths
        genome_size (int): Genome size in base pairs
        
    Returns:
        dict: Depth calculation results
    """
    logger = logging.getLogger(__name__)
    
    total_reads = 0
    total_bases = 0
    read_lengths = []
    
    # Process each read file
    for read_file in read_files:
        logger.info(f"Processing {read_file}")
        read_count, bases, avg_length = count_reads_and_bases(read_file)
        total_reads += read_count
        total_bases += bases
        read_lengths.append(avg_length)
    
    # Calculate statistics
    avg_read_length = sum(read_lengths) / len(read_lengths) if read_lengths else 0
    sequencing_depth = total_bases / genome_size if genome_size > 0 else 0
    
    results = {
        'total_reads': total_reads,
        'total_bases': total_bases,
        'avg_read_length': avg_read_length,
        'genome_size': genome_size,
        'sequencing_depth': sequencing_depth,
        'read_files_processed': len(read_files)
    }
    
    logger.info(f"Total reads: {total_reads:,}")
    logger.info(f"Total bases: {total_bases:,}")
    logger.info(f"Average read length: {avg_read_length:.1f} bp")
    logger.info(f"Genome size: {genome_size:,} bp")
    logger.info(f"Estimated sequencing depth: {sequencing_depth:.2f}x")
    
    return results

def write_depth_results(results, output_file):
    """
    Write depth calculation results to output file.
    
    Args:
        results (dict): Depth calculation results
        output_file (str): Path to output file
    """
    logger = logging.getLogger(__name__)
    
    try:
        with open(output_file, 'w') as f:
            f.write("# Read Depth Analysis Results\n")
            f.write(f"total_reads\t{results['total_reads']}\n")
            f.write(f"total_bases\t{results['total_bases']}\n")
            f.write(f"average_read_length\t{results['avg_read_length']:.2f}\n")
            f.write(f"genome_size\t{results['genome_size']}\n")
            f.write(f"sequencing_depth\t{results['sequencing_depth']:.2f}\n")
            f.write(f"read_files_processed\t{results['read_files_processed']}\n")
            
            # Add interpretation
            f.write("\n# Depth Interpretation\n")
            depth = results['sequencing_depth']
            if depth >= 50:
                interpretation = "High coverage - excellent for most analyses"
            elif depth >= 20:
                interpretation = "Good coverage - suitable for most analyses"
            elif depth >= 10:
                interpretation = "Moderate coverage - may be sufficient for basic analyses"
            elif depth >= 5:
                interpretation = "Low coverage - limited analysis capabilities"
            else:
                interpretation = "Very low coverage - may not be suitable for analysis"
            
            f.write(f"coverage_interpretation\t{interpretation}\n")
        
        logger.info(f"Depth results written to {output_file}")
        
    except Exception as e:
        logger.error(f"Error writing depth results: {e}")
        sys.exit(1)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Calculate sequencing depth using selected genome size"
    )
    parser.add_argument(
        '--reads', '-r',
        nargs='+',
        required=True,
        help="Input FASTQ files (can be gzipped)"
    )
    parser.add_argument(
        '--genome_info', '-g',
        required=True,
        help="Genome information file from pick_smallest_genome.py"
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help="Output file for depth calculation results"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger = setup_logging()
    
    # Validate input files
    for read_file in args.reads:
        if not Path(read_file).exists():
            logger.error(f"Read file not found: {read_file}")
            sys.exit(1)
    
    if not Path(args.genome_info).exists():
        logger.error(f"Genome info file not found: {args.genome_info}")
        sys.exit(1)
    
    # Parse genome information
    genome_info = parse_genome_info(args.genome_info)
    if genome_info is None:
        logger.error("Failed to parse genome information")
        sys.exit(1)
    
    genome_size = genome_info['estimated_genome_size']
    
    # Calculate depth
    results = calculate_depth(args.reads, genome_size)
    
    # Write results
    write_depth_results(results, args.output)
    
    logger.info("Depth calculation completed successfully")

if __name__ == "__main__":
    main()