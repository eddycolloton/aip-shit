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

def process_path(path, csv_writer):
    """Processes a given file or directory, adding checksums to the CSV, ignoring hidden files."""
    if os.path.isfile(path):
        if not is_hidden_file(path):  # Check if the file is hidden
            checksum = hashlib_md5(path)
            row_data = {'Filename': path, 'MD5 Checksum': checksum}
            csv_writer.writerow(row_data)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                filepath = os.path.join(root, file)
                if not is_hidden_file(filepath):  # Check if the file is hidden
                    checksum = hashlib_md5(filepath)
                    row_data = {'Filename': filepath, 'MD5 Checksum': checksum}
                    csv_writer.writerow(row_data)

def main():
    """Main function to handle command-line arguments and script execution."""
    parser = argparse.ArgumentParser(description="Collect MD5 checksums of files and directories.")
    parser.add_argument("path", help="File or directory to process")
    parser.add_argument("output", nargs="?", default="checksums.csv", 
                        help="Output CSV file path (default: checksums.csv)")
    args = parser.parse_args()

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