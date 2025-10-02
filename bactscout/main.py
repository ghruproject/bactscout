from bactscout.preflight import check_databases, check_software, check_system_resources, load_config
from bactscout.util import print_header, print_message
import os 
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from bactscout.thread import run_one_sample

def main(input_dir, output_dir, max_threads, config_file: str = "bactscout_config.yml"):
    config = load_config(config_file)
    print_header("Preflight Checks")
    check_system_resources(config)
    check_software(config)
    check_databases(config)
    print_header("Running Pipeline")
    
    # Get all sample pairs
    sample_pairs = locate_read_file_pairs(input_dir)
    total_samples = len(sample_pairs)
    
    if total_samples == 0:
        print_message("No FASTQ file pairs found in input directory", "error")
        return
    
    print_message(f"Found {total_samples} sample pairs to process", "info")
    print_message(f"Using up to {max_threads} parallel threads", "info")
    
    # Process samples in parallel using ThreadPoolExecutor
    successful_samples = []
    failed_samples = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task(f"Processing {total_samples} samples...", total=total_samples)
        
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            # Submit all samples for processing
            future_to_sample = {
                executor.submit(run_one_sample, sample, reads['R1'], reads['R2'], output_dir, config, False): sample
                for sample, reads in sample_pairs.items()
            }
            
            # Process completed tasks as they finish
            for future in as_completed(future_to_sample):
                sample = future_to_sample[future]
                try:
                    result = future.result()
                    if result and result.get('status') == 'success':
                        successful_samples.append(sample)
                    else:
                        failed_samples.append(sample)
                        print_message(f"❌ Sample {sample} failed", "error")
                except (RuntimeError, OSError, ValueError) as exc:
                    failed_samples.append(sample)
                    print_message(f"❌ Sample {sample} generated an exception: {exc}", "error")                
                # Update progress
                progress.update(task, advance=1)
    
    # Print final summary
    print_header("Pipeline Summary")
    print_message(f"Total samples processed: {total_samples}", "info")
    print_message(f"Successful: {len(successful_samples)}", "success")
    print_message(f"Failed: {len(failed_samples)}", "error" if failed_samples else "info")
    
    if failed_samples:
        print_message(f"Failed samples: {', '.join(failed_samples)}", "warning")


def locate_read_file_pairs(directory):
    """
    Locate and return pairs of read files in the specified directory.

    Args:
        directory (str): Path to the directory containing FASTQ files. 
    """
    read_pairs = {}
    for filename in os.listdir(directory):
        if filename.endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz")):
            base_name = filename.split("_R1")[0] if "_R1" in filename else filename.split("_R2")[0]
            if base_name not in read_pairs:
                read_pairs[base_name] = {}
            if "_R1" in filename:
                read_pairs[base_name]['R1'] = os.path.join(directory, filename)
            elif "_R2" in filename:
                read_pairs[base_name]['R2'] = os.path.join(directory, filename)
    # Filter out incomplete pairs
    complete_pairs = {k: v for k, v in read_pairs.items() if 'R1' in v and 'R2' in v}
    return complete_pairs
