import os
import csv
import argparse
import sys
from pathlib import Path

def get_file_size(file_path):
    """Get the size of a file in bytes."""
    try:
        return os.path.getsize(file_path)
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error accessing {file_path}: {e}", file=sys.stderr)
        return 0

def format_size(size_bytes):
    """Format file size in a human-readable format."""
    # Convert bytes to appropriate unit
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0 or unit == 'TB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

def process_path(path, csv_writer, raw_sizes=False):
    """Process a file or directory and write to CSV."""
    path = Path(path)
    
    if path.is_file():
        size = get_file_size(path)
        size_to_write = size if raw_sizes else format_size(size)
        csv_writer.writerow([str(path), size_to_write])
    elif path.is_dir():
        for root, _, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                size = get_file_size(file_path)
                size_to_write = size if raw_sizes else format_size(size)
                csv_writer.writerow([str(file_path), size_to_write])
    else:
        print(f"Error: {path} is not a valid file or directory", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description='Create a CSV file with filenames and their sizes.')
    parser.add_argument('path', help='Path to file or directory')
    parser.add_argument('-o', '--output', default='file_sizes.csv', 
                        help='Output CSV file name (default: file_sizes.csv)')
    parser.add_argument('--raw', action='store_true', 
                        help='Store raw byte sizes instead of human-readable format')
    parser.add_argument('-a', '--append', action='store_true',
                        help='Append to existing CSV instead of creating a new one')
    
    args = parser.parse_args()
    
    # Determine file mode based on output
    if os.path.exists(args.output):
        file_mode = 'a'
    else:
        file_mode = 'w'

    
    # Check if we need to write headers (only for new files)
    write_header = file_mode == 'w'
    
    with open(args.output, file_mode, newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # Write header row if creating a new file
        if write_header:
            csv_writer.writerow(['File Path', 'Size'])
        
        process_path(args.path, csv_writer, args.raw)
    
    print(f"File information has been saved to {args.output}")

if __name__ == '__main__':
    main()