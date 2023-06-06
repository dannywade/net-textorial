import ipaddress
import json
import os
import streamlit as st
from dotenv import load_dotenv
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
from netmiko.ssh_autodetect import SSHDetect

load_dotenv()

class NetworkDevice:
    def __init__(self, host_id: str, credentials: dict, device_type: str):
        self.host_id = host_id
        self.credentials = credentials
        self.device_type = device_type
        self.connection = None

    def device_connection(self):
        remote_device = {
            "device_type": self.device_type,
            "host": self.host_id,
            "username": self.credentials.get("Username"),
            "password": self.credentials.get("Password"),
        }
        if self.device_type == "autodetect":
            try:
                guesser = SSHDetect(**remote_device)
                best_match = guesser.autodetect()
                remote_device["device_type"] = best_match
            except NetmikoTimeoutException as e:
                st.exception(e)
                self.connection = None
            except NetmikoAuthenticationException as e:
                st.exception(e)
                self.connection = None
        try:
            self.connection = ConnectHandler(**remote_device)
        except NetmikoTimeoutException as e:
            st.exception(e)
            self.connection = None
        except NetmikoAuthenticationException as e:
            st.exception(e)
            self.connection = None

    def get_device_info(self, user_input):
        command_list = user_input.split(" ")
        try:
            ipaddress.ip_address(command_list[0])
            host = command_list[0]
        except ValueError:
            host = command_list[0]

        if self.connection is not None:
            try:
                if command_list[1] != "show":
                    raise Exception("Only 'show' commands are supported.")
                else:
                    raw_output = self.connection.send_command((" ".join(command_list[1:])))
                    parsed_output = self.connection.send_command((" ".join(command_list[1:])), use_textfsm=True)
                    if not parsed_output:
                        parsed_output = "N/A"
            except (NetmikoTimeoutException, NetmikoAuthenticationException, Exception) as e:
                st.exception(e)
                raw_output = None
                parsed_output = None
        else:
            raw_output = None
            parsed_output = None

        if raw_output and ("invalid input" in raw_output.lower() or "invalid command" in raw_output.lower()):
            raw_output = "Invalid command sent to the device."
            parsed_output = None

        if parsed_output and "\n" in parsed_output:
            parsed_output = None
        else:
            try:
                iter(parsed_output)
                parsed_output = json.dumps(parsed_output, indent=2)
            except TypeError:
                pass

        return raw_output, parsed_output
