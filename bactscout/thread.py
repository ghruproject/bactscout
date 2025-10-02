import os
from bactscout.software.run_ariba import run_command as run_ariba
from bactscout.software.run_fastp import run_command as run_fastp
from bactscout.software.run_sylph import run_command as run_sylph, extract_species_from_report
from bactscout.util import print_message


def run_one_sample(sample_id, read1_file, read2_file, output_dir, config, message=False):
    """Run analysis for a single sample."""
    try:
        if message:
            print_message(f"Running analysis for {sample_id}", "info")

        fastp_output_dir = f"{output_dir}/{sample_id}/fastp"
        # Create output directory if it doesn't exist
        if not os.path.exists(fastp_output_dir):
            os.makedirs(fastp_output_dir, exist_ok=True)
            
        sylph_result = run_sylph(read1_file, read2_file, fastp_output_dir, config)
        species = extract_species_from_report(sylph_result.get('sylph_report', ''))
        fastp_result = run_fastp(read1_file, read2_file, fastp_output_dir, config)
        ariba_result = None
        if len(species) == 1: 
            species = species[0]
            # Run ARIBA if a single species is identified
            # Need to determine the species_db path
            species_key = None
            for key, value in config['ariba_species'].items():
                if value == species:
                    species_key = key
                    break
            
            if species_key:
                species_db_path = os.path.join(config['bactscout_dbs_path'], species_key, 'ref_db')
                ariba_output_dir = os.path.join(fastp_output_dir, 'ariba')
                ariba_result = run_ariba(read1_file, read2_file, species_db_path, ariba_output_dir, config)
        return {
            'status': 'success',
            'sample_id': sample_id,
            'fastp_result': fastp_result,
            'sylph_result': sylph_result,
            'ariba_result': ariba_result,
            'species': species
        }
        
    except (FileNotFoundError, PermissionError, OSError) as e:
        if message:
            print_message(f"Error processing sample {sample_id}: {str(e)}", "error")
        return {
            'status': 'failed',
            'sample_id': sample_id,
            'error': str(e)
        }
