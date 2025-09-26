#!/usr/bin/env python3
"""
Helper script to pick the smallest genome size from sylph profile output.
This script parses the sylph output and selects the species with the smallest genome size.
"""

import argparse
import pandas as pd
import sys
import logging

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def parse_sylph_profile(input_file):
    """
    Parse sylph profile output and extract genome sizes.
    
    Args:
        input_file (str): Path to the sylph profile TSV file
        
    Returns:
        pandas.DataFrame: Parsed data with species and genome size information
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Read the TSV file
        df = pd.read_csv(input_file, sep='\t')
        logger.info(f"Successfully read {len(df)} entries from {input_file}")
        
        # Check if required columns exist
        required_columns = ['Genome_name', 'ANI_to_query', 'Containment_to_query']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Column '{col}' not found in input file. Available columns: {list(df.columns)}")
        
        # Filter for high-quality matches (ANI > 80% and containment > 0.1)
        if 'ANI_to_query' in df.columns and 'Containment_to_query' in df.columns:
            filtered_df = df[
                (df['ANI_to_query'] > 80.0) & 
                (df['Containment_to_query'] > 0.1)
            ].copy()
            logger.info(f"Filtered to {len(filtered_df)} high-quality matches")
        else:
            filtered_df = df.copy()
            logger.warning("Using all entries due to missing quality columns")
            
        if len(filtered_df) == 0:
            logger.warning("No high-quality matches found, using all entries")
            filtered_df = df.copy()
            
        return filtered_df
        
    except Exception as e:
        logger.error(f"Error parsing sylph profile: {e}")
        return pd.DataFrame()

def extract_genome_size(genome_name):
    """
    Extract genome size from GTDB genome name format.
    GTDB names often contain size information in the format: GCF_000001405.40_GRCh38.p14_genomic_3031042516
    
    Args:
        genome_name (str): GTDB genome name
        
    Returns:
        float: Estimated genome size in base pairs (or 0 if not found)
    """
    logger = logging.getLogger(__name__)
    
    # Try to extract size from the end of the genome name
    parts = genome_name.split('_')
    
    # Look for numeric part that could be genome size
    for part in reversed(parts):
        if part.isdigit() and len(part) > 6:  # Genome sizes are typically > 1M bp
            size = int(part)
            if size > 100000:  # Reasonable minimum genome size
                return size
    
    # Default estimates based on common species patterns
    genome_name_lower = genome_name.lower()
    
    # Bacterial genome size estimates (approximate)
    if any(term in genome_name_lower for term in ['escherichia', 'e.coli']):
        return 4600000  # ~4.6 Mb
    elif any(term in genome_name_lower for term in ['staphylococcus', 'staph']):
        return 2800000  # ~2.8 Mb
    elif any(term in genome_name_lower for term in ['streptococcus', 'strep']):
        return 2000000  # ~2.0 Mb
    elif any(term in genome_name_lower for term in ['salmonella']):
        return 4900000  # ~4.9 Mb
    elif any(term in genome_name_lower for term in ['pseudomonas']):
        return 6300000  # ~6.3 Mb
    elif any(term in genome_name_lower for term in ['klebsiella']):
        return 5400000  # ~5.4 Mb
    elif any(term in genome_name_lower for term in ['bacillus']):
        return 4200000  # ~4.2 Mb
    elif any(term in genome_name_lower for term in ['listeria']):
        return 2900000  # ~2.9 Mb
    elif any(term in genome_name_lower for term in ['campylobacter']):
        return 1600000  # ~1.6 Mb
    else:
        # Default bacterial genome size
        logger.warning(f"Could not determine genome size for {genome_name}, using default 3.5 Mb")
        return 3500000  # Default ~3.5 Mb

def select_smallest_genome(df):
    """
    Select the genome with the smallest size from the filtered results.
    
    Args:
        df (pandas.DataFrame): Filtered sylph profile data
        
    Returns:
        dict: Information about the selected genome
    """
    logger = logging.getLogger(__name__)
    
    if len(df) == 0:
        logger.error("No data to process")
        return None
    
    # Add genome size estimates
    df['estimated_genome_size'] = df['Genome_name'].apply(extract_genome_size)
    
    # Sort by genome size and select the smallest
    df_sorted = df.sort_values('estimated_genome_size')
    selected = df_sorted.iloc[0]
    
    result = {
        'genome_name': selected['Genome_name'],
        'estimated_size': int(selected['estimated_genome_size']),
        'ani': selected.get('ANI_to_query', 'N/A'),
        'containment': selected.get('Containment_to_query', 'N/A')
    }
    
    logger.info(f"Selected genome: {result['genome_name']} with estimated size: {result['estimated_size']:,} bp")
    
    return result

def write_output(selected_genome, output_file):
    """
    Write the selected genome information to output file.
    
    Args:
        selected_genome (dict): Selected genome information
        output_file (str): Path to output file
    """
    logger = logging.getLogger(__name__)
    
    try:
        with open(output_file, 'w') as f:
            f.write(f"selected_genome_name\t{selected_genome['genome_name']}\n")
            f.write(f"estimated_genome_size\t{selected_genome['estimated_size']}\n")
            f.write(f"ani_to_query\t{selected_genome['ani']}\n")
            f.write(f"containment_to_query\t{selected_genome['containment']}\n")
        
        logger.info(f"Results written to {output_file}")
        
    except Exception as e:
        logger.error(f"Error writing output: {e}")
        sys.exit(1)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Pick the smallest genome size from sylph profile output"
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help="Input sylph profile TSV file"
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help="Output file for selected genome information"
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
    
    # Parse input file
    df = parse_sylph_profile(args.input)
    
    if len(df) == 0:
        logger.error("No valid data found in input file")
        sys.exit(1)
    
    # Select smallest genome
    selected_genome = select_smallest_genome(df)
    
    if selected_genome is None:
        logger.error("Failed to select genome")
        sys.exit(1)
    
    # Write output
    write_output(selected_genome, args.output)
    
    logger.info("Genome selection completed successfully")

if __name__ == "__main__":
    main()