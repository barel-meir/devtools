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
    data = []
    # Initialize variables to hold data
    timestamp = None
    entry_data = []

    for line in lines:
        # Check if the line starts with a timestamp format
        if re.match(r'\d{10}\.\d+\s+', line):
            # If this is not the first entry, append the previous data to the list
            if timestamp is not None:
                data.append({"timestamp": timestamp, "data":   parse_section(entry_data)})

            # Extract timestamp
            timestamp = line.split()[0]
            # Reset entry data
            entry_data = []
        elif line.strip() and not line.startswith("                                ..."):  # Check if line is not empty
            entry_data.append(line)

    # Append the last entry
    if timestamp is not None:
        data.append({"timestamp": timestamp, "data": parse_section(entry_data)})

    return data


def main():
    # Example usage
    raw = """recipient_: 
   platform_id_: ""
   sensor_id_: ""
   payload_id_: ""
source_: 
   platform_id_: "4444"
   sensor_id_: ""
   payload_id_: ""
group_id_: ""
fcu_mode_: "POSCTL"
state_: 
   val_: 1
communication_status_: 0
velocity_: 
   linear_: 
      x_: 0.011879418045282364
      y_: 0.0093862051144242287
      z_: -0.016274377703666687
   angular_: 
      x_: 0.00053120854629462903
      y_: -0.00034977906565744258
      z_: -4.3460903150019216e-05
orientation_: 
   yaw_: 301.019989
   pitch_: 0.184050187
   roll_: 0.273557574
stamp_: 
   sec_: 1714999415
   nanosec_: 458338526
position_: 
   latitude_: 32.1486132
   longitude_: 34.8543296
   altitude_: 64.369
home_position_: 
   latitude_: 32.148612900000003
   longitude_: 34.854328099999996
   altitude_: 72.084999999999994
battery_state_: 
   header_: 
      stamp_: 
         sec_: 1714999415
         nanosec_: 28129912
      frame_id_: ""
   voltage_: 49.0040016
   temperature_: 0
   current_: 17.4599991
   charge_: nan
   capacity_: nan
   design_capacity_: 0
   percentage_: 93
   power_supply_status_: 2
   power_supply_health_: 0
   power_supply_technology_: 3
   present_: true
   cell_voltage_: 
      [0]: 4.08300018
      [1]: 4.08300018
      [2]: 4.08300018
      [3]: 4.08300018
      [4]: 4.08300018
      [5]: 4.08300018
      [6]: 4.08300018
      [7]: 4.08300018
      [8]: 4.08300018
      [9]: 4.08300018
   cell_temperature_: 
   location_: "id1"
   serial_number_: ""
mission_data_: 
   id_: ""
   lut_: 1714998204199
   state_: 
      val_: 7
is_connected_to_ground_station_: false
is_ground_station_exists_: false
failure_: 
   val_: 0
platform_mode_: 
   val_: 2
battery_times_: 
   seconds_to_pre_bingo_: 
      sec_: 9999
      nanosec_: 0
   seconds_to_bingo_: 
      sec_: 9999
      nanosec_: 0
   seconds_to_critical_bingo_: 
      sec_: 9999
      nanosec_: 0
   seconds_to_dead_battery_: 
      sec_: 0
      nanosec_: 0
emergencyLandingData_: NULL
is_armed_: false
pre_takeoff_ready_state_: 
   val_: 1
navigation_status_: 
   stamp_: 
      sec_: 1714999414
      nanosec_: 2638392963
   navigation_source_: 
      val_: 5
   anchor_source_: 
      val_: 0
   images_available_: true
   telemetry_available_: true
   gps_jam_: false
   gps_spoof_: true
   asio_ready_: true
   estimated_delta_: 0
   slam_quality_: 0
   helios_voter_state_: 
      val_: 3"""

    filename = "ddsSpyEcorder-06-05-24_15-43-28.log"  # Replace with your file name
    with open(filename, 'r') as file:
        lines = file.readlines()[12:]

    json_data = parse_file(lines)
    print(json.dumps(json_data, indent=4))
    with open("parsed_data.json", 'w') as json_file:
        json.dump(json_data, json_file, indent=4)


if __name__ == "__main__":
    main()
