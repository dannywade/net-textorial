import ipaddress
import json
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import os
from rich.syntax import Syntax
from rich.text import Text
import pyperclip
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Content, Container
from textual.widgets import Static, Input, Footer, Button
from textual_autocomplete._autocomplete import AutoComplete, Dropdown

# local imports
from helpers import device_connection, get_items
from inventory import InventorySidebar


class NetTextorialApp(App):
    """Get info from network device"""

    CSS_PATH = "net.css"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "copy_raw", "Copy raw output"),
        Binding("p", "copy_parsed", "Copy parsed output"),
        Binding("i", "inventory", "Inventory"),
    ]

    def action_toggle_sidebar(self) -> None:
        """Called when user hits 'b' key."""
        self.show_bar = not self.show_bar

    def action_copy_raw(self) -> None:
        """Called when user hits 'r' key. Copies the raw command output."""
        # Queries for widget that holds raw results
        raw_output = self.query_one("#raw-results")
        # Extracts text from 'Syntax' renderable and copies to clipboard
        raw_output = str(raw_output.render().code)
        pyperclip.copy(raw_output)

    def action_copy_parsed(self) -> None:
        """Called when user hits 'p' key. Copies the parsed command output."""
        # Queries for widget that holds parsed results
        parsed_output = self.query_one("#parsed-results")
        # Extracts text from 'Syntax' renderable and copies to clipboard
        parsed_output = str(parsed_output.render().code)
        pyperclip.copy(parsed_output)

    def compose(self) -> ComposeResult:
        yield Container(
            AutoComplete(
                Input(
                    placeholder="Enter device hostname/IP and command: '<hostname/IP> show <command>'",
                    id="command_input",
                ),
                Dropdown(
                    items=get_items,  # Using a callback to dynamically generate items
                    id="my-dropdown",
                ),
            ),
            Button(label="Go!", variant="primary", id="run_button"),
            id="input_container",
        )
        yield Content(
            Static(Text("Raw Output", justify="center"), classes="result-header"),
            Static(id="raw-results", classes="result"),
            classes="results-container",
        )
        yield Content(
            Static(Text("Parsed Output", justify="center"), classes="result-header"),
            Static(id="parsed-results", classes="result"),
            classes="results-container",
        )
        yield Footer()
        self.inventory = InventorySidebar(classes="hidden")
        yield self.inventory

    def on_mount(self) -> None:
        """Called when app starts."""
        # Give the input focus, so we can start typing straight away
        self.query_one("#command_input").focus()

    # def on_input_submitted(self, message: Input.Submitted) -> None:
    #     """Runs when user hits enter"""
    #     if message.value:
    #         # Get user input when 'Enter' key is pressed
    #         self.get_device_info(message.value)

    def on_button_pressed(self, _: Button.Pressed) -> None:
        """Run when user clicks 'Go!' button"""
        user_input = self.query_one("#command_input")
        if user_input.value:
            # Get user input when user clicks 'Go!' button
            self.get_device_info(user_input.value)

    def action_inventory(self) -> None:
        """Toggle the display of the inventory sidebar"""
        if self.inventory.shown:
            self.inventory.hide()
        else:
            self.inventory.show()

    def get_device_info(self, user_input) -> None:
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

        raw_results = Syntax(
            raw_output, "teratermmacro", theme="nord", line_numbers=True
        )
        parsed_results = Syntax(
            parsed_output, "teratermmacro", theme="nord", line_numbers=True
        )
        self.query_one("#raw-results", Static).update(raw_results)
        self.query_one("#parsed-results", Static).update(parsed_results)


if __name__ == "__main__":
    app = NetTextorialApp()
    app.run()
