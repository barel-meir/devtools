import json
import re
import csv


def parse_tree(lines):
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


def pre_process(lines: [str]):
    for i in range(len(lines)):
        leading_space = len(lines[i]) - len(lines[i].lstrip())
        if leading_space > 0:
            for j in range(int(leading_space / 3)):
                lines[i] = f" {lines[i]}"
        lines[i] = lines[i].replace("\n", "")
        lines[i] = lines[i].replace("\"", "")

    return lines


def transform_to_json(key_value_str):
    key, value = key_value_str.split(':')
    value = format_value(value)

    key_parts = key.split('.')

    # Build the nested structure for the JSON
    json_data = {}
    current_dict = json_data
    for part in key_parts[:-1]:
        current_dict[part] = {}
        current_dict = current_dict[part]

    if type(value) == str:
        current_dict[key_parts[-1]] = value.strip()
    else:
        current_dict[key_parts[-1]] = value

    return json_data


def concat_nested_dicts(dict1, dict2):
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


def format_value(value):
    try:
        if "nan" != value.strip():
            value = float(value)
    except ValueError:
        # keet as str
        pass
    return value


def parse_section(lines):
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
            spliited = key_chained.split(".")
            key_chain_level = len(spliited)
            if nested_section_flag and key_chain_level == level + 1:
                key_chained = ".".join(spliited[:-1])
            nested_section_flag = False
            key_chained = f"{key_chained}.{key}"
        elif level > 0 and not name.endswith("_: "):
            tmp_dict = transform_to_json(f"{key_chained}.{key}: {value}")
            output = concat_nested_dicts(tmp_dict, output)
            nested_section_flag = True

    return output


def parse_file(lines):
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


def is_valid_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return False
    return True


def parse_dds_spy_record_to_json(input_filename: str):
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


def create_csv(json_data, nested_patterns_str, csv_file):
    nested_patterns = [pattern_str.split('.') for pattern_str in nested_patterns_str]
    # Open the CSV file in write mode
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write header row with specific column names
        writer.writerow(['Pattern', 'Value'])

        # Iterate over each entry in the JSON data
        for entry in json_data:
            # Check if the entry matches any of the nested patterns
            for pattern in nested_patterns:
                # Search for the pattern within the entry
                value = entry
                for key in pattern:
                    if key in value:
                        value = value[key]
                    else:
                        value = None
                        break

                # If the pattern is found, create a CSV row
                if value is not None:
                    writer.writerow(['.'.join(pattern), value])


def main():
    input_filename = "example_data/subsample_2.log"
    csv_file_name = f"output-{input_filename.split('.')[0]}.csv"
    nested_patterns_str = ['battery_state_.voltage_', 'communication_status_', 'source_.platform_id_']

    json_data = parse_dds_spy_record_to_json(input_filename)
    # create_csv(json_data, nested_patterns_str, csv_file_name)


# timestamp, batterytimes,position,

if __name__ == "__main__":
    main()
