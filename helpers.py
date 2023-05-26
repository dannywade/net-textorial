import ipaddress
import json
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)
from netmiko import ConnectHandler
from netmiko.ssh_autodetect import SSHDetect
import os
from dotenv import load_dotenv

load_dotenv()


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


def get_device_info(user_input) -> tuple:
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