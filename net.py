import json
import os
import requests
from rich.syntax import Syntax
from rich.tree import Tree
from pathlib import Path
import pyperclip
from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll, Container
from textual.widgets import Static, Input, Footer, Button, Tabs
from textual.worker import get_current_worker
from textual_autocomplete import AutoComplete, Dropdown

# from textual_autocomplete._autocomplete import AutoComplete, Dropdown

# local imports
from helpers import get_device_info, add_node, get_items, write_json_file
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
            # Clear results box and provide useful feedback to user
            self.query_one("#output-results", Static).update(
                "Please wait... ChatGPT is analyzing the JSON payload."
            )
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
            # Ask ChatGPT to analyze JSON
            self.ai_chat(f"Tell me about this JSON payload: {self.json_data}")

    @work(exclusive=True)
    def ai_chat(self, prompt: str) -> str:
        """Ask ChatGPT a question. Assumes API key is set as an environment variable"""
        api_key = os.getenv("OPEN_AI_KEY")
        worker = get_current_worker()
        chatgpt_widget = self.query_one("#output-results", Static)

        if prompt and api_key is not None:
            response = requests.post(
                url="https://api.openai.com/v1/chat/completions",
                headers={"authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            chatgpt_results = Text.from_ansi(
                response.json()["choices"][0]["message"]["content"]
            )
            if not worker.is_cancelled:
                # Update widget from thread
                self.call_from_thread(chatgpt_widget.update, chatgpt_results)
        else:
            # No result from ChatGPT, return blank
            if not worker.is_cancelled:
                self.call_from_thread(
                    chatgpt_widget.update,
                    "Sorry, no OpenAI API key was found. Please make sure to set an environment variable.",
                )


if __name__ == "__main__":
    app = NetTextorialApp()
    app.run()
