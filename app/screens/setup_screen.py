from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Static

from app.utils.config import Config


class SetupScreen(Screen[None]):
    """Shown when the app is missing Telegram API credentials."""

    def __init__(self, config: Config, details: str = "") -> None:
        super().__init__()
        self.config = config
        self.details = details

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="screen-shell screen-center"):
            with Vertical(classes="card"):
                yield Label("Telegram API Setup", id="login-title")
                yield Static("Create a .env file in the project root with these values:")
                yield Static("TELEGRAM_API_ID=123456\nTELEGRAM_API_HASH=your_api_hash_here")
                yield Static(
                    "Get your API credentials from https://my.telegram.org/apps",
                    classes="setup-copy",
                )
                yield Static(
                    f"Expected .env path:\n{self.config.env_path}",
                    classes="setup-copy",
                )
                if self.details:
                    with VerticalScroll(classes="setup-details"):
                        yield Static(self.details, classes="setup-copy")
        yield Footer()
