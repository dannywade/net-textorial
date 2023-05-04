import asyncio
import json
from rich.syntax import Syntax
from rich.tree import Tree
from pathlib import Path
import pyperclip
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll, Container
from textual.widgets import Static, Input, Footer, Button, Tabs, Tab
from textual_autocomplete import AutoComplete, Dropdown

# from textual_autocomplete._autocomplete import AutoComplete, Dropdown

# local imports
from helpers import ai_chat, get_device_info, add_node, get_items, write_json_file
from inventory import InventorySidebar, InventoryScreen


class NetTextorialApp(App):
    """Get info from network device"""

    CSS_PATH = "net.css"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "copy_output", "Copy output"),
        Binding("i", "inventory", "Inventory"),
        Binding("v", "push_screen('inventory')", "Inventory Page"),
    ]
    SCREENS = {"inventory": InventoryScreen()}

    def action_toggle_sidebar(self) -> None:
        """Called when user hits 'b' key."""
        self.show_bar = not self.show_bar

    def action_copy_output(self) -> None:
        """Called when user hits 'r' key. Copies the raw command output."""
        # Queries for widget that holds raw results
        raw_output = self.query_one("#output-results")
        tabs = self.query(Tabs).first()
        # Figures out whether the 'Parsed Output (tree)' tab is currently active
        if tabs.validate_active("tab-3"):
            output = "Manually copy tree output from app."
        else:
            # Extracts text from 'Syntax' renderable and copies to clipboard
            output = str(raw_output.render().code)
        pyperclip.copy(output)

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
        yield VerticalScroll(
            Tabs(
                "Raw Output",
                "Parsed Output",
                "Parsed Output (tree)",
                "Learn with ChatGPT",
                id="output-tabs",
            ),
            Static(id="output-results", classes="result"),
            classes="results-container",
        )
        yield Footer()
        self.inventory = InventorySidebar(classes="hidden")
        yield self.inventory

    def on_mount(self) -> None:
        """Called when app starts."""
        # Give the input focus, so we can start typing straight away
        self.query_one("#command_input").focus()
        # Initialize outputs
        self.raw_output = ""
        self.parsed_output = ""

    def on_button_pressed(self, _: Button.Pressed) -> None:
        """Run when user clicks 'Go!' button"""
        user_input = self.query_one("#command_input")
        if user_input.value:
            # Get user input when user clicks 'Go!' button
            outputs = get_device_info(user_input.value)
            self.raw_output = outputs[0]
            self.parsed_output = outputs[1]
            # Write parsed output to local JSON file
            write_json_file("parsed_output", self.parsed_output)

    def action_inventory(self) -> None:
        """Toggle the display of the inventory sidebar"""
        if self.inventory.shown:
            self.inventory.hide()
        else:
            self.inventory.show()

    async def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle TabActivated message sent by Tabs."""
        # Raw Output tab
        if event.tab.id == "tab-1":
            self.query_one("#output-results", Static).update(
                Syntax(
                    self.raw_output, "teratermmacro", theme="nord", line_numbers=True
                )
            )
        # Parsed Output tab
        elif event.tab.id == "tab-2":
            # Load the JSON file
            file_path = Path(__file__).parent / "parsed_output.json"
            with open(file_path) as parsed_data:
                self.parsed_output = json.load(parsed_data)
            # Convert loaded JSON to string for display
            parsed_jstring = json.dumps(self.parsed_output, indent=2)
            self.query_one("#output-results", Static).update(
                Syntax(
                    parsed_jstring,
                    "teratermmacro",
                    theme="nord",
                    line_numbers=True,
                )
            )
        # Parsed Output (tree) tab
        elif event.tab.id == "tab-3":
            # Load the JSON file
            try:
                file_path = Path(__file__).parent / "parsed_output.json"
                with open(file_path) as parsed_data:
                    self.json_data = json.load(parsed_data)
            except:
                self.query_one("#output-results", Static).update(
                    "Local JSON file could not be loaded. Please ensure parsed output is available."
                )
                return
            # Update the correct tab
            tree: Tree[dict] = Tree("Parsed Output")
            # json_node = tree.add("Parsed Output")
            tree = add_node("Parsed Output", tree, self.json_data)
            self.query_one("#output-results", Static).update(tree)
        # Learn with ChatGPT tab
        elif event.tab.id == "tab-4":
            # Load the JSON file, if not already loaded
            try:
                file_path = Path(__file__).parent / "parsed_output.json"
                with open(file_path) as parsed_data:
                    self.json_data = json.load(parsed_data)
            except:
                self.query_one("#output-results", Static).update(
                    "Local JSON file could not be loaded. Please ensure parsed output is available."
                )
                return
            loop = asyncio.get_running_loop()
            # Placeholder while ChatGPT loads answer
            self.query_one("#output-results", Static).update(f"Waiting for ChatGPT...")
            # Ask ChatGPT to explain the parsed output
            result = await loop.run_in_executor(
                None, ai_chat, f"Tell me about this JSON payload: {self.json_data}"
            )
            # Show ChatGPT results
            if result:
                self.query_one("#output-results", Static).update(
                    f"ChatGPT response: \n\n{result['choices'][0]['message']['content']}"
                )
            else:
                self.query_one("#output-results", Static).update(
                    "ChatGPT is currently not responding..."
                )


if __name__ == "__main__":
    app = NetTextorialApp()
    app.run()
