
import csv
from pathlib import Path

def summary_dir(data_dir, output_file):
    """
    Read the data/output dir, each folder inside is a sample, each folder has a summary.csv file. 
    Merge these into a single summary.csv file.
    
    Args:
        data_dir (str): Path to directory containing sample subdirectories
        output_file (str): Path to output merged CSV file
    """
    
    # Convert to Path objects for easier manipulation
    data_path = Path(data_dir)
    output_path = Path(output_file)
    
    # Find all CSV files that match the pattern *_summary.csv
    summary_files = []
    
    # Look for summary CSV files in each subdirectory
    for sample_dir in data_path.iterdir():
        if sample_dir.is_dir():
            # Look for CSV files in this sample directory
            for csv_file in sample_dir.glob("*_summary.csv"):
                summary_files.append(csv_file)
    
    if not summary_files:
        print(f"No summary CSV files found in {data_dir}")
        return
    
    print(f"Found {len(summary_files)} summary files to merge")
    
    # Read the first file to get the header
    header = None
    all_rows = []
    
    for csv_file in sorted(summary_files):
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                if not rows:
                    print(f"Warning: Empty file {csv_file}")
                    continue
                
                # Use the first file's header as the master header
                if header is None:
                    header = rows[0]
                    print(f"Using header from {csv_file}")
                
                # Add data rows (skip header)
                if len(rows) > 1:
                    all_rows.extend(rows[1:])
                    print(f"Added {len(rows)-1} rows from {csv_file}")
                else:
                    print(f"Warning: No data rows in {csv_file}")
                    
        except (IOError, OSError, UnicodeDecodeError) as e:
            print(f"Error reading {csv_file}: {e}")
            continue
    
    # Write the merged file
    try:
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            if header:
                writer.writerow(header)
            
            # Write all data rows
            writer.writerows(all_rows)
        
        print(f"Successfully merged {len(all_rows)} rows into {output_file}")
        print(f"Total samples processed: {len(all_rows)}")
        
    except (IOError, OSError) as e:
        print(f"Error writing merged file {output_file}: {e}")
        raise

