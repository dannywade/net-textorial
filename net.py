from __future__ import annotations

import json


from rich.syntax import Syntax

from textual.app import App, ComposeResult
from textual.containers import Content
from textual.widgets import Static, Input

from napalm import get_network_driver


class NetApp(App):
    """Get info from network device"""

    CSS_PATH = "net.css"

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Enter device name and item, ex 'eos1 config'")
        yield Content(Static(id="results"), id="results-container")

    def on_mount(self) -> None:
        """Called when app starts."""
        # Give the input focus, so we can start typing straight away
        self.query_one(Input).focus()

    def on_input_submitted(self, message: Input.Submitted) -> None:
        """Runs when user hits enter"""
        if message.value:
            # Look up the word in the background
            self.get_device_info(message.value)

    def get_device_info(self, items) -> None:
        """Terrible looking function with a bunch of if statements"""
        things = items.split(" ")
        driver = get_network_driver("eos")
        with driver(things[0], "admin", "admin") as device:
            if things[1] == "config":
                stuff = device.get_config()["running"]

            elif things[1] == "facts":
                stuff = json.dumps(device.get_facts(), indent=2)

            elif things[1] == "diff":
                device.load_merge_candidate(filename=f"configs/{things[0]}.cfg")
                stuff = device.compare_config()

            elif things[1] == "interfaces":
                stuff = json.dumps(device.get_interfaces(), indent=2)

            elif things[1] == "cli":
                command = device.cli([" ".join(things[2:])])
                stuff = command[f"{' '.join(things[2:])}"]
            else:
                stuff = f"Sorry, '{things[1]}' is not supported"

        syntax = Syntax(stuff, "teratermmacro", theme="nord", line_numbers=True)
        self.query_one("#results", Static).update(syntax)


if __name__ == "__main__":
    app = NetApp()
    app.run()
