import os
import sys
import platform
import hashlib
import csv
import argparse

def hashlib_md5(filename):
    '''
    Create an md5 checksum.
    '''
    read_size = 0
    last_percent_done = 0
    md5_object = hashlib.md5()
    total_size = os.path.getsize(filename)
    print(f'Generating md5 checksum for {os.path.basename(filename)}')
    with open(str(filename), 'rb') as file_object:
        while True:
            buf = file_object.read(2**20)
            if not buf:
                break
            read_size += len(buf)
            md5_object.update(buf)
            percent_done = 100 * read_size / total_size
            if percent_done > last_percent_done:
                sys.stdout.write('[%d%%]\r' % percent_done)
                sys.stdout.flush()
                last_percent_done = percent_done
    md5_output = md5_object.hexdigest()
    print(f'Calculated md5 checksum is {md5_output}\n')
    return md5_output

## The function above, hashlib_md5 is a slightly modified version of the function from the open-source project IFIscripts
## More here: https://github.com/Irish-Film-Institute/IFIscripts/blob/master/scripts/copyit.py
## IFIscripts license information below:
# The MIT License (MIT)
# Copyright (c) 2015-2018 Kieran O'Leary for the Irish Film Institute.
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.


def is_hidden_file(filepath):
    """Checks if a file is hidden on macOS or Windows."""
    name = os.path.basename(filepath)
    return (
        name.startswith('.')  # macOS hidden files start with '.'
        or has_hidden_attribute(filepath)  # Windows hidden files have the 'hidden' attribute
    )

def is_system_file(filepath):
    """Checks if a file is a system file on Windows or macOS."""
    if platform.system() == 'Windows':
        try:
            import win32con, win32api
            attrs = win32api.GetFileAttributes(filepath)
            return attrs & win32con.FILE_ATTRIBUTE_SYSTEM != 0
        except ImportError:
            # If win32api is not available, use some common Windows system file patterns
            name = os.path.basename(filepath).lower()
            system_patterns = [
                'thumbs.db', 'desktop.ini', '$recycle.bin', 'system volume information',
                'pagefile.sys', 'hiberfil.sys', 'swapfile.sys'
            ]
            return any(pattern in name for pattern in system_patterns)
    elif platform.system() == 'Darwin':  # macOS
        # Common macOS system files/directories
        system_patterns = [
            '.ds_store', '.localized', '.spotlight-v100', '.trashes', '.fseventsd'
        ]
        name = os.path.basename(filepath).lower()
        return any(pattern == name for pattern in system_patterns)
    elif platform.system() == 'Linux':
        # Common Linux system directories/files to ignore
        system_patterns = [
            '/proc/', '/sys/', '/dev/', '/run/', '/tmp/', 
            'lost+found', '.gvfs'
        ]
        return any(pattern in filepath.lower() for pattern in system_patterns)
    return False

def has_hidden_attribute(filepath):
    """Checks if a file has the 'hidden' attribute on Windows."""
    if platform.system() == 'Windows':
        try:
            import win32con, win32api
            attrs = win32api.GetFileAttributes(filepath)
            return attrs & win32con.FILE_ATTRIBUTE_HIDDEN != 0
        except ImportError:
            # win32api might not be available on all Windows installations
            return False
    else:
        return False  # Not on Windows

def should_ignore_file(filepath):
    """Determines if a file should be ignored based on hidden and system status."""
    return is_hidden_file(filepath) or is_system_file(filepath)

def process_path(path, csv_writer):
    """Processes a given file or directory, adding checksums to the CSV, ignoring hidden and system files."""
    if os.path.isfile(path):
        if not should_ignore_file(path):  # Check if the file should be ignored
            checksum = hashlib_md5(path)
            row_data = {'Filename': path, 'MD5 Checksum': checksum}
            csv_writer.writerow(row_data)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            # Modify dirs in-place to avoid walking into hidden/system directories
            dirs[:] = [d for d in dirs if not should_ignore_file(os.path.join(root, d))]
            
            for file in files:
                filepath = os.path.join(root, file)
                if not should_ignore_file(filepath):  # Check if the file should be ignored
                    checksum = hashlib_md5(filepath)
                    row_data = {'Filename': filepath, 'MD5 Checksum': checksum}
                    csv_writer.writerow(row_data)

def main():
    """Main function to handle command-line arguments and script execution."""
    parser = argparse.ArgumentParser(description="Collect MD5 checksums of files and directories.")
    parser.add_argument("path", help="File or directory to process")
    parser.add_argument("output", nargs="?", default="checksums.csv", 
                        help="Output CSV file path (default: checksums.csv)")
    parser.add_argument("--include-hidden", action="store_true",
                        help="Include hidden files in the checksum calculation")
    parser.add_argument("--include-system", action="store_true",
                        help="Include system files in the checksum calculation")
    args = parser.parse_args()

    # Override the should_ignore_file function based on command-line arguments
    global should_ignore_file
    original_should_ignore_file = should_ignore_file
    
    def custom_should_ignore_file(filepath):
        is_hidden = is_hidden_file(filepath)
        is_system = is_system_file(filepath)
        
        # Only ignore if appropriate based on flags
        if is_hidden and not args.include_hidden:
            return True
        if is_system and not args.include_system:
            return True
        return False
    
    # Replace the function with our custom version
    should_ignore_file = custom_should_ignore_file

    csv_filename = args.output
    file_exists = os.path.isfile(csv_filename)

    with open(csv_filename, "a", newline="") as csvfile:
        fieldnames = ["Filename", "MD5 Checksum"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        process_path(args.path, writer)

if __name__ == "__main__":
    main()