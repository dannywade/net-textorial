import datetime
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Label, Switch, Input, Button

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
        yield Container(
            Vertical(
                Label("Netbox", classes="chkbox-label"), Switch(id="netbox_checkbox")
            ),
            Vertical(
                Label("Nautobot", classes="chkbox-label"),
                Switch(id="nautobot_checkbox"),
            ),
            Vertical(
                Label("DNAC", classes="chkbox-label"),
                Switch(id="dnac_checkbox"),
            ),
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

    def on_checkbox_changed(self, event: Switch.Changed) -> None:
        """Check if SoT is being used for autocompletion and toggle inputs"""
        netbox_checkbox = self.query_one("#netbox_checkbox")
        nautobot_checkbox = self.query_one("#nautobot_checkbox")
        dnac_checkbox = self.query_one("#dnac_checkbox")
        msg = self.query_one("#sync_message")
        chkbox_values = [
            netbox_checkbox.value,
            nautobot_checkbox.value,
            dnac_checkbox.value,
        ]
        if all(chkbox_values):
            # 'Disable' inputs for user
            self.query_one("#sot_url").add_class("disabled-text")
            self.query_one("#sot_api_token").add_class("disabled-text")
            self.query_one("#sot_sync_button").disabled = True
            # Add helpful error message to user
            msg.renderable = Text("Please only select one SoT!", style="orchid")
            msg.refresh()
        elif netbox_checkbox.value:
            # Clear any error messages
            msg.renderable = ""
            msg.refresh()
            # 'Enable' inputs for user
            self.query_one("#sot_url").remove_class("disabled-text")
            self.query_one("#sot_api_token").remove_class("disabled-text")
            self.query_one("#sot_sync_button").disabled = False
        elif nautobot_checkbox.value:
            # Clear any error messages
            msg.renderable = ""
            msg.refresh()
            # 'Enable' inputs for user
            self.query_one("#sot_url").remove_class("disabled-text")
            self.query_one("#sot_api_token").remove_class("disabled-text")
            self.query_one("#sot_sync_button").disabled = False
        elif dnac_checkbox.value:
            # Clear any error messages
            msg.renderable = ""
            msg.refresh()
            # 'Enable' inputs for user
            self.query_one("#sot_url").remove_class("disabled-text")
            self.query_one("#sot_api_token").remove_class("disabled-text")
            self.query_one("#sot_sync_button").disabled = False
        else:
            # Clear any error messages
            msg.renderable = ""
            msg.refresh()
            # 'Disable' inputs for user
            self.query_one("#sot_url").add_class("disabled-text")
            self.query_one("#sot_api_token").add_class("disabled-text")
            self.query_one("#sot_sync_button").disabled = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Sync with source of truth (SoT) and provide user with helpful message whether sync was successful"""
        # Retrieve URL and API token from user
        sot_url = self.query_one("#sot_url", Input)
        api_token = self.query_one("#sot_api_token", Input)
        if self.query_one("#netbox_checkbox").value:
            source = "netbox"
        elif self.query_one("#nautobot_checkbox").value:
            source = "nautobot"
        elif self.query_one("#dnac_checkbox").value:
            source = "dnac"
        nb_sync = sot_sync(sot_url.value, api_token.value, source)
        sync_msg = self.query_one("#sync_message")
        last_sync_msg = self.query_one("#last_synced")
        if nb_sync:
            sync_msg.renderable = Text("Sync was successful", style="green1")
            current_time = datetime.datetime.now()
            last_sync_msg.renderable = Text(
                f"Last synced: {current_time}", style="#a1a1a1"
            )
            last_sync_msg.refresh()
        else:
            sync_msg.renderable = Text("Sync was not successful", style="red1")
        sync_msg.refresh()
