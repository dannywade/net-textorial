import json
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)
from netmiko import ConnectHandler
from netmiko.ssh_autodetect import SSHDetect
import os
import pynetbox
from rich.text import Text
from textual_autocomplete._autocomplete import DropdownItem


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


def netbox_sync(url: str, token: str) -> bool:
    """
    Gathers the following device info from Netbox:
        - Name
        - Primary IP
        - Device type

    Args:
        url (str): Netbox instance URL
        token (str): Netbox API token

    Returns:
        Boolean
    """
    if url and token:
        # User must provide URL and API token
        # Builds query objects for Netbox
        nb = pynetbox.api(url, token)
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
    except pynetbox.RequestError:
        return False

    # Serializing json
    json_object = json.dumps(device_list, indent=4)

    # Writing to sample.json
    with open("netbox_inventory.json", "w") as outfile:
        outfile.write(json_object)
        inv_filepath = os.path.dirname(os.path.abspath(__file__))

    # Confirm inventory file was created and exists - return True or False
    inv_file_exists = os.path.exists(f"{inv_filepath}/netbox_inventory.json")

    return inv_file_exists


def get_items(value: str, cursor_position: int) -> list[DropdownItem]:
    """Attempt to read local inventory file (JSON) and build list of DropdownItems to use for autocomplete

    Args:
        value (str): Automatically received by Input widget included in the AutoComplete container
        cursor_position (int): Automatically received by Input widget included in the AutoComplete container
    """

    try:
        with open(f"./netbox_inventory.json", "r") as f:
            nb_devices = json.load(f)
    except FileNotFoundError:
        return ""

    items = []

    for dev in nb_devices:
        items.append(
            DropdownItem(
                Text(dev.get("name")),  # 'main' column
                Text(dev.get("primary_ip"), style="#a1a1a1"),
                Text(dev.get("device_type"), style="#a1a1a1"),
            )
        )

    # Only keep cities that contain the Input value as a substring
    matches = [c for c in items if value.lower() in c.main.plain.lower()]

    # Favor items that start with the Input value, pull them to the top
    ordered = sorted(matches, key=lambda v: v.main.plain.startswith(value.lower()))

    return ordered
