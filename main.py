import json
import re
import csv
from typing import Union


def parse_tree(lines: [str]) -> (int, str, str):
    """
    Parse an indented outline into (level, name, parent) tuples.  Each level
    of indentation is 4 spaces.
    """
    regex = re.compile(r'^(?P<indent>(?: {4})*)(?P<name>\S.*)')
    stack = []
    for line in lines:
        match = regex.match(line)
        if not match:
            raise ValueError(
                'Indentation not a multiple of 4 spaces: "{0}"'.format(line)
            )
        level = len(match.group('indent')) // 4
        if level > len(stack):
            raise ValueError('Indentation too deep: "{0}"'.format(line))
        stack[level:] = [match.group('name')]
        yield level, match.group('name'), (stack[level - 1] if level else None)


def pre_process(lines: [str]) -> [str]:
    """
    Pre-process the input lines to ensure consistent indentation and remove unnecessary characters.
    :param lines: strings list represents the original dds spy file content
    :return: strings list represents the processed dds spy file content
    """
    for i in range(len(lines)):
        leading_space = len(lines[i]) - len(lines[i].lstrip())
        if leading_space > 0:
            for j in range(int(leading_space / 3)):
                lines[i] = f" {lines[i]}"
        lines[i] = lines[i].replace("\n", "")
        lines[i] = lines[i].replace("\"", "")

    return lines


def transform_to_json(key_value_str: str) -> dict:
    """
    Transform a string containing key-value pairs into nested JSON format.
        (example: 'source_.platform_id_: 6181.0')

    :param key_value_str: String containing key-value pairs separated by a colon.
    :return: Nested JSON object representing the key-value pairs.
    """
    key, value = key_value_str.split(':')
    value = format_value(value)

    key_parts = key.split('.')

    # Build the nested structure for the JSON
    json_data = {}
    current_dict = json_data
    for part in key_parts[:-1]:
        current_dict[part] = {}
        current_dict = current_dict[part]

    if type(value) is str:
        current_dict[key_parts[-1]] = value.strip()
    else:
        current_dict[key_parts[-1]] = value

    return json_data


def concat_nested_dicts(dict1: dict, dict2: dict) -> dict:
    """
    Concatenate two nested dictionaries, preserving the structure of both dictionaries.

    :param dict1: First nested dictionary
    :param dict2: Second nested dictionary
    :return: Concatenated nested dictionary.
    """
    result = {}
    for key, value in dict1.items():
        if isinstance(value, dict) and key in dict2:
            result[key] = concat_nested_dicts(value, dict2[key])
        else:
            result[key] = dict2.get(key, value)
    for key, value in dict2.items():
        if key not in dict1:
            result[key] = value
    return result


def format_value(value: str) -> Union[float, str]:
    """
        Convert the input value to a float if possible; otherwise, keep it as a string.

    :param value: Input value to be formatted.
    :return: Formatted value as a float or string.
    """
    try:
        if "nan" != value.strip():
            value = float(value)
    except ValueError:
        pass
    return value


def parse_section(lines: [str]) -> dict:
    """
        Parse a section of indented lines into nested JSON format.

    :param lines: List of input lines representing a section of indented data.
    :return: Nested JSON object representing the parsed section.
    """
    lines = pre_process(lines)
    output = {}
    key_chained = ""
    nested_section_flag = False
    for level, name, parent in parse_tree(lines):
        key, value = map(str.strip, name.split(':', 1))
        value = format_value(value)
        if level == 0 and not name.endswith("_: "):
            output[key] = value
            key_chained = ""
        elif level == 0 and name.endswith("_: "):
            key_chained = f"{key}"
            output[key] = {}
        elif level > 0 and name.endswith("_: "):
            split_key_chained = key_chained.split(".")
            key_chain_level = len(split_key_chained)
            if nested_section_flag and key_chain_level == level + 1:
                key_chained = ".".join(split_key_chained[:-1])
            nested_section_flag = False
            key_chained = f"{key_chained}.{key}"
        elif level > 0 and not name.endswith("_: "):
            split_key_chained = key_chained.split(".")
            key_chain_level = len(split_key_chained)
            while key_chain_level > 1 and split_key_chained[-1] != parent.split(":")[0]:
                key_chained = ".".join(split_key_chained[:-1])
                split_key_chained = key_chained.split(".")
                key_chain_level = len(split_key_chained)

            tmp_dict = transform_to_json(f"{key_chained}.{key}: {value}")
            output = concat_nested_dicts(tmp_dict, output)
            nested_section_flag = True

    return output


def parse_file(lines: [str]) -> dict:
    """
        Parse the entire input file into a dictionary of timestamped JSON data.

    :param lines:  List of input lines from the file.
    :return: Dictionary containing timestamped JSON data.
    """
    data = {}
    # Initialize variables to hold data
    timestamp = None
    entry_data = []

    for line in lines:
        # Check if the line starts with a timestamp format
        if re.match(r'\d{10}\.\d+\s+', line):
            # If this is not the first entry, append the previous data to the list
            if timestamp is not None and entry_data:
                data[timestamp] = parse_section(entry_data)

            # Extract timestamp
            timestamp = line.split()[0]
            # Reset entry data
            entry_data = []
        elif line.strip() and not line.startswith("                                ..."):  # Check if line is not empty
            entry_data.append(line)

    # Append the last entry
    if timestamp is not None and entry_data:
        data[timestamp] = parse_section(entry_data)

    return data


def is_valid_json_file(file_path: str) -> bool:
    """
        Check if the file at the given path contains valid JSON data.

    :param file_path: Path to the file to be checked.
    :return: True if the file contains valid JSON; otherwise, False.
    """
    try:
        with open(file_path, 'r') as file:
            json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return False
    return True


def parse_dds_spy_record_to_json(input_filename: str) -> dict:
    """
        Parse the DDS Spy record file into JSON format and save the parsed data to a JSON file.

    :param input_filename: Path to the DDS Spy record file.
    :return: Dictionary containing the parsed JSON data.
    """
    output_filename = "output_data/parsed_data.json"

    with open(input_filename, 'r') as file:
        lines = file.readlines()[12:]

    json_data = parse_file(lines)
    with open(output_filename, 'w') as json_file:
        print(f'saving parsed data tp {output_filename}')
        json.dump(json_data, json_file, indent=4)

    if is_valid_json_file(output_filename):
        print(f"The file '{output_filename}' contains valid JSON.")
    else:
        print(f"The file '{output_filename}' does not contain valid JSON.")

    return json_data


def get_value_from_path(json_data: dict, path: str) -> Union[str, float, dict]:
    """
        Retrieve the value from the JSON data based on the provided path.

    :param json_data: JSON data to be traversed.
    :param path: Path specifying the location of the desired value.
    :return: Value retrieved from the JSON data.
    """
    keys = path.split(".")
    current_data = json_data
    try:
        for key in keys:
            if key.endswith("]"):
                key, index = key[:-1].split("[")
                index = int(index)
                current_data = current_data[key][f"[{index}]"]
            else:
                current_data = current_data[key]
        return current_data
    except KeyError:
        return ""


def create_csv(json_data: dict, nested_patterns_str: [str], csv_file: str) -> None:
    """
        Create a CSV file from the JSON data, extracting values based on the provided nested patterns.

    :param json_data: JSON data containing the information to be exported to CSV.
    :param nested_patterns_str: List of nested patterns specifying the data to be extracted.
    :param csv_file: Path to the CSV file to be created.
    :return: None
    """
    # Open the CSV file in write mode
    with open(csv_file, 'w', newline='') as csvfile:
        # Write header row with specific column names
        results = []
        fieldnames = ['Timestamp']

        # Iterate over each entry in the JSON data
        for entry in json_data:
            # Check if the entry matches any of the nested patterns
            current_dict = {"Timestamp": entry}
            for pattern in nested_patterns_str:
                # Search for the pattern within the entry
                value = get_value_from_path(json_data[entry], pattern)

                # If the pattern is found, create a CSV row
                if value is not None:
                    current_dict[pattern] = value
                    if pattern not in fieldnames:
                        fieldnames.append(pattern)
            results.append(current_dict)

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)


def main():
    """
    Main function to execute the parsing and CSV creation process.
    """

    input_filename = "example_data/subsample_2.log"
    csv_file_name = f"output-sss.csv"
    nested_patterns_str = ['battery_state_.voltage_', 'communication_status_', 'source_.platform_id_']

    json_data = parse_dds_spy_record_to_json(input_filename)
    create_csv(json_data, nested_patterns_str, csv_file_name)


if __name__ == "__main__":
    main()
