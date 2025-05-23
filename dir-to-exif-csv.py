import os
import sys
import json
import subprocess
import csv
from typing import Dict, List, Any, Set

def aggregate_exiftool(directory: str, output_csv: str = None) -> None:
    """
    Aggregate exiftool metadata for all image files in directory to a single CSV.
    
    :param directory: Path to directory containing image files
    :param output_csv: Path to output CSV file (optional)
    """
    # If no output path specified, create default in input directory
    if output_csv is None:
        output_csv = os.path.join(directory, 'exiftool_metadata.csv')
    
    # Comprehensive list of image file extensions
    image_extensions = [
        # Common image formats
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',
        '.heic', '.heif', '.avif', '.raw', '.cr2', '.nef', '.orf', '.sr2',
        '.dng', '.arw', '.rw2', '.psd', '.xcf', '.ai', '.svg', '.eps',
        
        # Additional image formats
        '.jfif', '.exif', '.ico', '.pcx', '.ppm', '.pbm', '.pgm', '.hdr',
        '.jp2', '.j2k', '.jpf', '.jpx', '.crw'
    ]
    
    # Collect exif data for all files
    all_exifdata = []
    
    for root, _, files in os.walk(directory):
        for filename in files:
            # Skip hidden files (starting with a dot)
            if filename.startswith('.'):
                continue
                
            # Skip system files (platform specific checks)
            if is_system_file(os.path.join(root, filename)):
                continue

            # Filter by file extensions (case-insensitive)
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                file_path = os.path.join(root, filename)
                
                try:
                    # Run exiftool with JSON output
                    result = subprocess.run(
                        ["exiftool", "-j", file_path], 
                        capture_output=True, 
                        text=True, 
                        check=True
                    )
                    
                    # Parse the JSON output (exiftool returns a JSON array)
                    exif_data = json.loads(result.stdout)
                    
                    # exiftool returns a list with one item per file
                    if exif_data and isinstance(exif_data, list):
                        for item in exif_data:
                            # Add relative path from the input directory for reference
                            rel_path = os.path.relpath(file_path, directory)
                            item['RelativePath'] = rel_path
                            all_exifdata.append(item)
                
                except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                    print(f"Error processing {file_path}: {e}")
    
    # If no files processed
    if not all_exifdata:
        print("No image files found in the directory.")
        return
    
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
    
    # Handle binary data fields for CSV compatibility
    def clean_binary_fields(record: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {}
        for key, value in record.items():
            # Check if the value contains "[binary data]" indication
            if isinstance(value, str) and "binary data" in value.lower():
                cleaned[key] = "[BINARY DATA]"
            else:
                cleaned[key] = value
        return cleaned
    
    # Clean all records
    cleaned_records = [clean_binary_fields(record) for record in all_exifdata]
    
    # Get comprehensive set of all possible keys
    all_keys: Set[str] = set()
    for record in cleaned_records:
        all_keys.update(record.keys())
    
    # Ensure certain fields come first in the CSV
    priority_fields = ['SourceFile', 'RelativePath', 'FileName', 'Directory', 
                      'FileSize', 'FileType', 'FileTypeExtension', 'MIMEType']
    
    # Create ordered list of keys
    ordered_keys = [field for field in priority_fields if field in all_keys]
    remaining_keys = sorted(key for key in all_keys if key not in priority_fields)
    all_ordered_keys = ordered_keys + remaining_keys
    
    # Write to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_ordered_keys, restval='')
        writer.writeheader()
        
        for record in cleaned_records:
            writer.writerow(record)
    
    print(f"Exiftool metadata aggregated to {output_csv}")
    print(f"Processed {len(cleaned_records)} image files with {len(all_ordered_keys)} metadata fields")

def main():
    # Check if directory path is provided
    if len(sys.argv) < 2:
        print("Usage: python exiftool-aggregator.py /path/to/directory [/path/to/output.csv]")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    # Optional output CSV path
    output_csv_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    aggregate_exiftool(directory_path, output_csv_path)

if __name__ == "__main__":
    main()
