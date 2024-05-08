import json
import re


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

    return lines


def transform_to_json(key_value_str):
    key, value = key_value_str.split(':')
    key_parts = key.split('.')

    # Build the nested structure for the JSON
    json_data = {}
    current_dict = json_data
    for part in key_parts[:-1]:
        current_dict[part] = {}
        current_dict = current_dict[part]
    current_dict[key_parts[-1]] = value.strip()

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


def parse_section(lines):
    lines = pre_process(lines)
    output = {}
    key_chained = ""
    for level, name, parent in parse_tree(lines):
        key, value = map(str.strip, name.split(':', 1))
        if level == 0 and not name.endswith("_: "):
            output[key] = value
            key_chained = ""
        elif level == 0 and name.endswith("_: "):
            key_chained = f"{key}"
            output[key] = {}
        elif level > 0 and name.endswith("_: "):
            key_chained = f"{key_chained}.{key}"
        elif level > 0 and not name.endswith("_: "):
            tmp_dict = transform_to_json(f"{key_chained}.{key}: {value}")
            output = concat_nested_dicts(tmp_dict, output)

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


def main():
    filename = "example_data/ddsSpyEcorder-06-05-24_15-43-28.log"
    with open(filename, 'r') as file:
        lines = file.readlines()[12:]

    json_data = parse_file(lines)
    print(json.dumps(json_data, indent=4))
    with open("output_data/parsed_data.json", 'w') as json_file:
        json.dump(json_data, json_file, indent=4)


if __name__ == "__main__":
    main()
