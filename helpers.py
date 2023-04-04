import ipaddress
import json
from math import ceil
from typing import Union
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)
from netmiko import ConnectHandler
from netmiko.ssh_autodetect import SSHDetect
import os
import pynetbox
import pynautobot
import requests
from rich.text import Text
from rich.tree import Tree

# from textual_autocomplete._autocomplete import DropdownItem, InputState


def device_connection(host_id: str, credentials: dict) -> ConnectHandler:
    """
    Automatically handles device connections using Netmiko.

    Args:
        host_id (str): Commonly the hostname of a network device
        credentials (dict): A dictionary with 'username' and 'password' as keys

    Returns:
        ConnectHandler object
    """
    remote_device = {
        "device_type": "autodetect",
        "host": host_id,
        "username": credentials.get("username"),
        "password": credentials.get("password"),
    }

    try:
        guesser = SSHDetect(**remote_device)
        best_match = guesser.autodetect()
        remote_device["device_type"] = best_match
        connection = ConnectHandler(**remote_device)
    except (
        NetmikoTimeoutException,
        NetmikoAuthenticationException,
    ) as e:
        print(f"Could not connect to device due to the following error: {e}")
        connection = None

    return connection


def get_device_info(self, user_input) -> tuple:
    """
    Allows user to run any CLI command and have the raw and parsed output returned.
    """

    command_list = user_input.split(" ")
    # Check whether entered host is an IP address or hostname
    # It won't matter now, but can provide simple validation in future.
    try:
        ipaddress.ip_address(command_list[0])
        host = command_list[0]
    except ValueError:
        host = command_list[0]
    host = command_list[0]
    # Try reading from env vars, default to admin/admin
    user = os.getenv("NET_TEXT_USER", "admin")
    pw = os.getenv("NET_TEXT_PASS", "admin")
    creds = {"username": user, "password": pw}
    dev_connect = device_connection(host_id=host, credentials=creds)
    if dev_connect is not None:
        try:
            if command_list[1] != "show":
                raise Exception("Only 'show' commands are supported.")
            else:
                with dev_connect as device:
                    raw_output = device.send_command((" ".join(command_list[1:])))
                    parsed_output = device.send_command(
                        (" ".join(command_list[1:])), use_textfsm=True
                    )
                    if not parsed_output:
                        parsed_output = "N/A"
        except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
            raw_output = f"There was an issue connecting to the device: {e}"
            parsed_output = "N/A"
        except Exception as e:
            raw_output = f"There was an error: {e}"
            parsed_output = "N/A"
    else:
        raw_output = "Could not connect to device."
        parsed_output = "N/A"

    # Cleanse the output if invalid command provided by user
    if "Invalid input detected" in raw_output:
        raw_output = "Invalid command sent to the device."
        parsed_output = "No parser available."
    # Convert parsed output to string and format
    if "\n" in parsed_output:
        # If newline characters are returned, there's a good chance there was not a parser available
        parsed_output = "No parser available."
    else:
        try:
            # Check if parsed_output is an iterable (dict, list, etc.) and convert to JSON string
            iter(parsed_output)
            parsed_output = json.dumps(parsed_output, indent=2)
        except TypeError:
            # parsed_output is not an iterable (most likely a string), so JSON string conversion is not necessary
            pass

    return raw_output, parsed_output


def sot_sync(url: str, token: str, source: str = None) -> bool:
    """
    Gathers the following device info from Netbox or Nautobot:
        - Name
        - Primary IP
        - Device type

    Args:
        url (str): Netbox/Nautobot instance URL
        token (str): Netbox/Nautobot API token
        source (str): Specifies the SoT system. Valid options include: "netbox" or "nautobot"

    Returns:
        Boolean
    """
    if source is None:
        # Source must be specified. Probably should add helpful error message
        return False

    if url and token:
        # User must provide URL and API token
        # Defer to helper function to collect DNAC inventory
        if source == "dnac":
            return dnac_inventory(url, token)
        # Builds query objects for Netbox or Nautobot
        if source == "netbox":
            nb = pynetbox.api(url, token)
        elif source == "nautobot":
            nb = pynautobot.api(url, token)
        else:
            # Invalid source was provided. Again, probably should add helpful error message
            return False
        # Extract device objs from SoT
        devices = nb.dcim.devices.all()
    else:
        return False

    device_list = []
    try:
        # Executes device collection and generates local JSON inventory file
        for device in devices:
            if device.name is not None and device.primary_ip is not None:
                device_obj = {
                    "name": str(device.name),
                    "primary_ip": str(device.primary_ip),
                    "device_type": str(device.device_type),
                }
                device_list.append(device_obj)
    except (pynetbox.RequestError, pynautobot.core.query.RequestError):
        return False

    # Serializing json
    json_object = json.dumps(device_list, indent=4)

    # Writing devices to JSON file
    with open("sot_inventory.json", "w") as outfile:
        outfile.write(json_object)
        inv_filepath = os.path.dirname(os.path.abspath(__file__))

    # Confirm inventory file was created and exists - return True or False
    inv_file_exists = os.path.exists(f"{inv_filepath}/sot_inventory.json")

    return inv_file_exists


### Disabled until textual autocomplete is compatible with Textual >=0.14.0 ###
# def get_items(input_state: InputState) -> list[DropdownItem]:
#     """Attempt to read local inventory file (JSON) and build list of DropdownItems to use for autocomplete

#     Args:
#         value (str): Automatically received by Input widget included in the AutoComplete container
#         cursor_position (int): Automatically received by Input widget included in the AutoComplete container
#     """

#     try:
#         with open(f"./sot_inventory.json", "r") as f:
#             nb_devices = json.load(f)
#     except FileNotFoundError:
#         return ""

#     items = []

#     for dev in nb_devices:
#         items.append(
#             DropdownItem(
#                 Text(dev.get("name")),  # 'main' column
#                 Text(dev.get("primary_ip"), style="#a1a1a1"),
#                 Text(dev.get("device_type"), style="#a1a1a1"),
#             )
#         )

#     # Only keep devices that contain the Input value as a substring
#     matches = [c for c in items if input_state.value.lower() in c.main.plain.lower()]

#     # Favor items that start with the Input value, pull them to the top
#     ordered = sorted(
#         matches, key=lambda v: v.main.plain.startswith(input_state.value.lower())
#     )

#     return ordered


def get_device_count(url: str, token: str) -> int:
    """Retrieve device count from DNAC inventory"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Auth-Token": token,
    }
    device_count_url = f"{url}/dna/intent/api/v1/network-device/count"
    response = requests.get(url=device_count_url, headers=headers, verify=False)
    if response.status_code == 200:
        device_count = response.json()["response"]
        return device_count
    else:
        # If device count API call fails, return 0
        return 0


def dnac_inventory(url: str, token: str) -> bool:
    """Retrieve all devices from DNAC inventory"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Auth-Token": token,
    }
    # Get total number of devices to figure out offset for larger inventories
    total_dev_count = get_device_count(url, token)
    if total_dev_count == 0:
        # If there are no devices or an error collecting the device count
        return False
    # Default and max limit for device inventory is 500, so we need to figure out how many API calls to make
    total_pages = ceil(total_dev_count / 500)
    # There's a hard limit to only return 500 devices per call, so we must change the params
    # if there's more than 500 devices in the inventory
    # Initialize device list
    device_list = []
    for page in range(total_pages):
        # Make additional calls (if necessary) - needed for inventories with more than 500 devices
        calc_offset = page * 500
        if calc_offset > 0:
            dnac_devices_url = (
                f"{url}/dna/intent/api/v1/network-device?limit=500&offset={calc_offset}"
            )
        else:
            # No offset needed
            dnac_devices_url = f"{url}/dna/intent/api/v1/network-device?limit=500"
        response = requests.get(
            url=dnac_devices_url,
            headers=headers,
            verify=False,
        )
        if response.status_code == 200:
            # Add devices to the response from the initial call
            device_list.extend(response.json()["response"])
        else:
            return False

        device_export = []
        # Time to create inventory JSON file
        try:
            # Executes device collection and generates local JSON inventory file
            for device in device_list:
                device_obj = {
                    "name": str(device.get("hostname")),
                    "primary_ip": str(device.get("managementIpAddress")),
                    "device_type": str(device.get("platformId")),
                }
                device_export.append(device_obj)
        except IndexError:
            # Assumes list is empty and avoids
            return False

        # Serializing json
        json_object = json.dumps(device_export, indent=4)

        # Writing devices to JSON file
        with open("sot_inventory.json", "w") as outfile:
            outfile.write(json_object)
            inv_filepath = os.path.dirname(os.path.abspath(__file__))

        # Confirm inventory file was created and exists - return True or False
        inv_file_exists = os.path.exists(f"{inv_filepath}/sot_inventory.json")

        return inv_file_exists


def load_inventory_file() -> list[dict]:
    """
    Loads JSON inventory file synced from SoT

    Example:
        [{'name': 'ams01-edge-01', 'primary_ip': '10.11.128.1/32', 'device_type': 'DCS-7280CR2-60'}, {'name': 'ams01-edge-02', 'primary_ip': '10.11.128.2/32', 'device_type': 'DCS-7280CR2-60'},...]
    """
    try:
        with open("sot_inventory.json") as json_file:
            data = json.load(json_file)
    except:
        data = []
    return data


def write_json_file(filename: str, output: Union[dict, list]) -> Tree:
    """Write parsed output to a JSON file"""
    with open(f"{filename}.json", "w") as output_file:
        json.dump(output, output_file, indent=2)


def add_node(name: str, tree: Tree, data: list) -> str:
    """Add nodes to Rich Tree renderable obj"""
    if isinstance(data, dict):
        tree.label = Text(f"{{}}")
        for key, value in data.items():
            new_node = tree.add(Text(f"{key} {{dict}}", style="bold red"))
            add_node(key, new_node, value)
    elif isinstance(data, list):
        tree.label = Text(f"{name} [list]", style="bold red")
        for index, value in enumerate(data):
            new_node = tree.add("")
            add_node(str(index), new_node, value)
    else:
        tree.add(Text(f"{data}", style="bold gold1"))

    return tree


def ai_chat(prompt: str) -> str:
    """Ask ChatGPT a question. Assumes API key is set as an environment variable"""
    api_key = os.getenv("OPEN_AI_KEY")

    response = requests.post(
        url="https://api.openai.com/v1/chat/completions",
        headers={"authorization": f"Bearer {api_key}"},
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    if response.status_code == 200:
        return response.json()
    else:
        return None
