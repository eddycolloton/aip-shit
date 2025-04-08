# aip-shit

This repo is currently a very informal landing place for scripts I am working on. 

## install

General python 3.x.x install instructions:

1. Make sure you have Python 3.x installed (3.0 or higher).
2. If you don't have `pip` installed, follow the instructions at <https://pip.pypa.io/en/stable/installation/>.
3. (Optionally create a virtual environment:)
   * `python -m venv my_checksum_env`
   * Activate the environment:
     * Windows: `my_checksum_env\Scripts\activate`
     * macOS/Linux: `source my_checksum_env/bin/activate`

## instructions

Each script has it's own functionality

### collect_checksums.py

Usage: `python collect_checksums.py <file_or_directory_path> <optional: csv output filename>`

If no csv output file name is provided, checksums are written to a file named "checksums.csv" in the current working directory.    

Example output included in this repo: `example_outputs/example_checksums.csv`   

### dir-to-exif-csv.py

Usage: `python dir-to-exif-csv.py <directory_path> <csv output filename>`

Both arguments are required    

Example output included in this repo: `example_outputs/exiftool_example.csv`   

### dir-to-mediainfo-csv.py

Usage: `python dir-to-mediainfo-csv.py <directory_path> <csv output filename>`

Both arguments are required    

Example output included in this repo: `example_outputs/mediainfo_example.csv`

