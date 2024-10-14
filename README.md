This repo is currently a very informal landing place for scripts I am working on. 

General python 3.x.x install instructions:

1. Make sure you have Python 3.x installed (3.0 or higher).
2. If you don't have `pip` installed, follow the instructions at <https://pip.pypa.io/en/stable/installation/>.
3. (Optionally create a virtual environment:)
   * `python -m venv my_checksum_env`
   * Activate the environment:
     * Windows: `my_checksum_env\Scripts\activate`
     * macOS/Linux: `source my_checksum_env/bin/activate`

To run collect_checksums.py

4. You can now run the script using: `python collect_checksums.py <file_or_directory_path>`

Example output included in this repo: checksums.csv