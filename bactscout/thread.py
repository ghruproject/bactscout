import os
from bactscout.software.run_stringmlst import run_command as run_mlst
from bactscout.software.run_fastp import run_command as run_fastp
from bactscout.software.run_sylph import run_command as run_sylph, extract_species_from_report
from bactscout.util import print_message
import json


def run_one_sample(sample_id, read1_file, read2_file, output_dir, config, message=False):
    """Run analysis for a single sample."""
    try:
        if message:
            print_message(f"Running analysis for {sample_id}", "info")

        sample_output_dir = f"{output_dir}/{sample_id}"
        # Create output directory if it doesn't exist
        if not os.path.exists(sample_output_dir):
            os.makedirs(sample_output_dir, exist_ok=True)
        final_results = {'sample_id': sample_id}
        sylph_result = run_sylph(read1_file, read2_file, sample_output_dir, config)
        species = extract_species_from_report(sylph_result.get('sylph_report', ''))
        fastp_result = run_fastp(read1_file, read2_file, sample_output_dir, config)
        fastp_stats = get_fastp_results(fastp_result)
        final_results.update(fastp_stats)
        coverage_cutoff = config.get('coverage_threshold', 30)
        
        final_results['species'] = ';'.join(species)
        if len(species) == 1: 
            species = species[0]
            final_results['species_status'] = 'PASSED'
            final_results['species_message'] = 'Single species detected.'
            # Run ARIBA if a single species is identified
            # Need to determine the species_db path
            species_key = None
            for key, value in config['mlst_species'].items():
                if value == species:
                    species_key = key
                    break
            
            if species_key:
                species_db_path = os.path.join(config['bactscout_dbs_path'], species_key, species_key)
                mlst_result = run_mlst(read1_file, read2_file, species_db_path, sample_output_dir, config)
                # Check MLST results
                if mlst_result.get('stringmlst_results', {}).get('ST'):
                    final_results['mlst_st'] = mlst_result['stringmlst_results']['ST']
                    final_results['mlst_status'] = 'PASSED'
                    final_results['mlst_message'] = f"Valid ST found: {mlst_result['stringmlst_results']['ST']}"
                else:
                    final_results['mlst_st'] = None
                    final_results['mlst_status'] = 'FAILED'
                    final_results['mlst_message'] = 'No valid ST found.'
            else:
                if message:
                    print_message(f"No MLST database found for species: {species}. Skipping MLST.", "warning")                
            # Get expected genome size, 
            expected_genome_size, gc_lower, gc_upper = get_expected_genome_size(species, config)
            # Get estimated coverage and eval fastp results
            if expected_genome_size > 0 and fastp_stats.get('total_bases', 0) > 0:
                estimated_coverage = fastp_stats['total_bases'] / expected_genome_size
            else:
                estimated_coverage = 0
            final_results['estimated_coverage'] = round(estimated_coverage, 2)
            final_results['expected_genome_size'] = expected_genome_size
            if estimated_coverage >= coverage_cutoff:
                final_results['coverage_status'] = 'PASSED'
                final_results['coverage_message'] = f'Estimated coverage {estimated_coverage:.2f}x meets the threshold of {coverage_cutoff}x.'
            else:
                final_results['coverage_status'] = 'FAILED'
                final_results['coverage_message'] = f'Estimated coverage {estimated_coverage:.2f}x below the threshold of {coverage_cutoff}x.'
            final_results['gc_content_lower'] = gc_lower
            final_results['gc_content_upper'] = gc_upper
            if gc_lower > 0 and gc_upper > 0:
                if gc_lower <= fastp_stats.get('gc_content', 0) <= gc_upper:
                    final_results['gc_content_status'] = 'PASSED'
                    final_results['gc_content_message'] = f'GC content {fastp_stats.get("gc_content", 0)}% within expected range ({gc_lower}-{gc_upper}%)'
                else:
                    final_results['gc_content_status'] = 'FAILED'
                    final_results['gc_content_message'] = f'GC content {fastp_stats.get("gc_content", 0)}% outside expected range ({gc_lower}-{gc_upper}%)'
            
        else:
            final_results['species_status'] = 'FAILED'
            final_results['species_message'] = 'Multiple or no species detected, skipping MLST and genome size estimation.'
        # Make the final output file with all the information
        # Write a csv file to the sample_output_dir
        final_output_file = os.path.join(sample_output_dir, f"{sample_id}_summary.csv")
        with open(final_output_file, 'w', encoding='utf-8') as f:
            # Write header
            headers = list(final_results.keys())
            f.write(','.join(headers) + '\n')
            # Write values
            values = [str(final_results[h]) if final_results[h] is not None else '' for h in headers]
            f.write(','.join(values) + '\n')


        return {
            'status': 'success',
            'sample_id': sample_id,
            'results': final_results,
        }
        
    except (FileNotFoundError, PermissionError, OSError) as e:
        if message:
            print_message(f"Error processing sample {sample_id}: {str(e)}", "error")
        return {
            'status': 'failed',
            'sample_id': sample_id,
            'error': str(e)
        }

def get_fastp_results(fastp_results):
    """
    Extract all 'after_filtering' values from fastp.json.
    """
    failed = {
            "total_reads": 0,
            "total_bases": 0,
            "q20_bases": 0,
            "q30_bases": 0,
            "q20_rate": 0.0,
            "q30_rate": 0.0,
            "read1_mean_length": 0,
            "read2_mean_length": 0,
            "gc_content": 0.0
        }
    if fastp_results.get('status') != 'success':
        return failed
    fastp_json = fastp_results.get('json_report')
    if not fastp_json or not os.path.exists(fastp_json):
        return failed

    with open(fastp_json, 'r') as f:
        data = json.load(f)

    after_filtering = data.get('summary').get('after_filtering', failed)
    after_filtering['gc_content'] = round(float(after_filtering['gc_content'] * 100), 4)
    return after_filtering


def get_expected_genome_size(species, config):
    """Get expected genome size for a given species from the filtered_metrics.csv."""
    metrics_file = config.get('metrics_file')
    safe_species_name = species.replace(' ', '_').replace('.', '_')
    genome_size = 0 
    gc_lower = 0 
    gc_upper = 0
    with open(metrics_file, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            # Line should be line Streptococcus_agalactiae,Genome_Size,<lower>,<upper>
            if line.startswith(safe_species_name) and 'Genome_Size' in line:
                genome_size = (int(parts[2]) + int(parts[2])) / 2
            # Also return GC Content, from Streptococcus_agalactiae,GC_Content,35,37 
            if line.startswith(safe_species_name) and 'GC_Content' in line:
                gc_lower = int(parts[2])
                gc_upper = int(parts[3])
    return genome_size, gc_lower, gc_upper

    