import os
import sys
import json
import subprocess
import csv
from typing import Dict, List, Any

def aggregate_mediainfo(directory: str, output_csv: str = None) -> None:
    """
    Aggregate mediainfo for all files in directory to a single CSV.
    
    :param directory: Path to directory containing media files
    :param output_csv: Path to output CSV file (optional)
    """
    # If no output path specified, create default in input directory
    if output_csv is None:
        output_csv = os.path.join(directory, 'mediainfo.csv')
    
    # Comprehensive list of media file extensions
    media_extensions = [
        # Video files
        '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.mpg', 
        '.mpeg', '.m2v', '.3gp', '.divx', '.rmvb', '.vob', '.ts', '.mts', '.m2ts', 
        
        # Audio files
        '.mp3', '.wav', '.flac', '.aac', '.wma', '.m4a', '.ogg', '.opus', 
        '.aiff', '.alac', '.ac3', '.mka',
        
        # Additional media file types
        '.asf', '.ogv', '.webp'
    ]
    
    # Collect media info for all files
    all_mediainfo = []
    
    for root, _, files in os.walk(directory):
        for filename in files:
            # Skip hidden files (starting with a dot)
            if filename.startswith('.'):
                continue
                
            # Skip system files (platform specific checks)
            if is_system_file(os.path.join(root, filename)):
                continue

            # Filter by file extensions (case-insensitive)
            if any(filename.lower().endswith(ext) for ext in media_extensions):
                file_path = os.path.join(root, filename)
                
                try:
                    # Run mediainfo with JSON output
                    result = subprocess.run(
                        ["mediainfo", "-f", "--Output=JSON", file_path], 
                        capture_output=True, 
                        text=True, 
                        check=True
                    )
                    
                    # Parse the JSON output
                    mediainfo_data = json.loads(result.stdout)
                    
                    # Add filename to the data for reference
                    mediainfo_data['filename'] = os.path.basename(file_path)
                    
                    all_mediainfo.append(mediainfo_data)
                
                except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                    print(f"Error processing {file_path}: {e}")
    
    # If no files processed
    if not all_mediainfo:
        print("No media files found in the directory.")
        return
    
        # Flatten and collect all unique keys
    def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.update(flatten_dict(v, new_key, sep=sep))
            elif isinstance(v, list):
                # Handle list of tracks specifically
                if k == 'track':
                    for idx, track in enumerate(v):
                        track_items = flatten_dict(track, f"{new_key}_{idx}", sep=sep)
                        items.update(track_items)
                else:
                    items[new_key] = json.dumps(v)
            else:
                items[new_key] = v
        return items
        
    # Flatten all records and get comprehensive set of keys
    flattened_records = [flatten_dict(record) for record in all_mediainfo]
    all_keys = set(key for record in flattened_records for key in record.keys())
    
    # Ensure 'filename' is the first column
    keys = ['filename'] + sorted(all_keys - {'filename'})
    
    # Write to CSV
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys, restval='N/A')
        writer.writeheader()
        
        for record in flattened_records:
            writer.writerow(record)
    
    print(f"Mediainfo aggregated to {output_csv}")


def is_system_file(file_path: str) -> bool:
    """
    Check if a file is a system file.

    This is a platform-specific check:
    - On Windows: Checks for hidden, system attributes
    - On macOS: Checks for specific system files and hidden flag
    - On Linux: Simple implementation (only hidden file check)

    :param file_path: Path to the file to check
    :return: True if it's a system file, False otherwise
    """
    # Get the file name (without path)
    filename = os.path.basename(file_path)

    # Common system files to ignore across platforms
    system_file_patterns = [
        'thumbs.db', 'desktop.ini', '.ds_store', 
        '$recycle.bin', '$RECYCLE.BIN', 
        'system volume information',
        '.Trashes', '.Spotlight-V100', '.fseventsd'
    ]

    # Check against common system file patterns (case insensitive)
    if any(pattern in filename.lower() for pattern in system_file_patterns):
        return True
        
    # Platform-specific checks
    if sys.platform == 'win32':
        try:
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)
            # Check if file has hidden or system attribute
            if attrs != -1 and (attrs & 2 or attrs & 4):  # 2=Hidden, 4=System
                return True
        except (ImportError, AttributeError):
            # If ctypes not available or function call fails
            pass

    elif sys.platform == 'darwin':  # macOS
        try:
            import stat
            st = os.stat(file_path)
            # Check if file has hidden flag (UF_HIDDEN)
            if st.st_flags & 0x8000:  # UF_HIDDEN = 0x8000
                return True
        except (ImportError, AttributeError, OSError):
            pass

    # For Linux and other systems, we rely on the hidden file check (done earlier)

    return False

def main():
    # Check if directory path is provided
    if len(sys.argv) < 2:
        print("Usage: python script.py /path/to/directory [/path/to/output.csv]")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    # Optional output CSV path
    output_csv_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    aggregate_mediainfo(directory_path, output_csv_path)

if __name__ == "__main__":
    main()
