import datetime
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Input, Button, RadioSet

# local imports
from helpers import sot_sync


class InventorySidebar(Vertical):
    """Inventory sidebar"""

    def compose(self) -> ComposeResult:
        """
        Compose the inventory sidebar

        Returns:
            ComposeResult: The layout of the inventory sidebar
        """
        yield Label("Inventory (SoT)", id="sot_header", classes="h1")
        yield RadioSet(
            "Netbox",
            "Nautobot",
            "DNAC",
            id="sot_selector_container",
        )
        yield Label("Inventory URL", classes="h2")
        yield Input(
            placeholder="https://<url>:<port>",
            id="sot_url",
            classes="disabled-text",
        )
        yield Label("API token", classes="h2")
        yield Input(
            placeholder="abcd1234....",
            password=True,
            id="sot_api_token",
            classes="disabled-text",
        )
        yield Button(
            label="Sync", disabled=True, variant="success", id="sot_sync_button"
        )
        yield Label(id="sync_message")
        yield Label(id="success_message")
        yield Label(Text("Last synced: -", style="#a1a1a1"), id="last_synced")

    def on_mount(self) -> None:
        """Hide the inventory options"""
        self.hide()

    def hide(self) -> None:
        """Hide the inventory options."""
        self.add_class("hidden")

    def show(self) -> None:
        """Show the inventory options."""
        self.remove_class("hidden")

    @property
    def shown(self) -> bool:
        """Confirm whether inventory is being shown"""
        return not self.has_class("hidden")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Check if SoT is being used for autocompletion and toggle inputs"""
        # Get the RadioButton widget that was selected
        self.sot_selected = event.pressed
        # Enable URL/API token textboxes and Sync button
        self.query_one("#sot_url").remove_class("disabled-text")
        self.query_one("#sot_api_token").remove_class("disabled-text")
        self.query_one("#sot_sync_button").disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Sync with source of truth (SoT) and provide user with helpful message whether sync was successful"""
        # Retrieve URL and API token from user
        sot_url = self.query_one("#sot_url", Input)
        api_token = self.query_one("#sot_api_token", Input)
        sync_msg = self.query_one("#sync_message")
        last_sync_msg = self.query_one("#last_synced")
        if sot_url.value and api_token.value:
            nb_sync = sot_sync(
                sot_url.value, api_token.value, self.sot_selected.label.plain.lower()
            )
        else:
            nb_sync = False
            sync_msg.update(Text("Please fill out all fields!", style="gold1"))
            return
        if nb_sync:
            sync_msg.update(Text("Sync was successful", style="green1"))
            current_time = datetime.datetime.now()
            last_sync_msg.update(Text(f"Last synced: {current_time}", style="#a1a1a1"))
        else:
            sync_msg.update(Text("Sync was not successful", style="red1"))
