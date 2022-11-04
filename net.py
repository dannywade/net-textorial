import ipaddress
import json
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import os
from rich.syntax import Syntax
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Content
from textual.widgets import Static, Input
# local imports
from helpers import device_connection


class NetApp(App):
    """Get info from network device"""

    CSS_PATH = "net.css"

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Enter device hostname/IP and command: '<hostname/IP> show <command>'")
        yield Content(Static(Text("Raw Output", justify="center"), classes="result-header"), Static(id="raw-results", classes="result"), classes="results-container")
        yield Content(Static(Text("Parsed Output", justify="center"), classes="result-header"), Static(id="parsed-results", classes="result"), classes="results-container")

    def on_mount(self) -> None:
        """Called when app starts."""
        # Give the input focus, so we can start typing straight away
        self.query_one(Input).focus()

    def on_input_submitted(self, message: Input.Submitted) -> None:
        """Runs when user hits enter"""
        if message.value:
            # Get user input when 'Enter' key is pressed
            self.get_device_info(message.value)

    def get_device_info(self, user_input) -> None:
        """
        Allows user to run any CLI command and have the raw and parsed output returned.
        """
        
        command_list = user_input.split(" ")
        print(command_list)
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
                            parsed_output = device.send_command((" ".join(command_list[1:])), use_textfsm=True)
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

        raw_results = Syntax(raw_output, "teratermmacro", theme="nord", line_numbers=True)
        parsed_results = Syntax(parsed_output, "teratermmacro", theme="nord", line_numbers=True)
        self.query_one("#raw-results", Static).update(raw_results)
        self.query_one("#parsed-results", Static).update(parsed_results)


if __name__ == "__main__":
    app = NetApp()
    app.run()
