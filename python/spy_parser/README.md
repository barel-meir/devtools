# DDS Spy Parser

The DDS Spy Parser is a Python script that parses DDS Spy record files and creates CSV files based on the specified nested patterns.

## Usage

```bash
python dds_spy_parser.py [-h] [--input input_filename] [--output csv_file_name] [--patterns nested_patterns_str [nested_patterns_str ...]]
``` 
## Description
Parse DDS Spy record file and create CSV.

### Optional Arguments
* -h, --help: Show help message and exit.
* --input input_filename: Input filename.
* --output csv_file_name: CSV output filename.
* --patterns nested_patterns_str [nested_patterns_str ...]: List of nested patterns.

#### example:
```bash 
python dds_spy_parser.py --input ddsSpyEcorder-09-09-18_19-53-28.log --output bareli.csv --patterns position_.latitude_ position_.longitude_ position_.altitude_
```
