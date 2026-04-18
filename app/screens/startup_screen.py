from __future__ import annotations

from textual.css.query import NoMatches
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, LoadingIndicator, Static


class StartupScreen(Screen[None]):
    """Initial loading screen shown while the Telegram client connects."""

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="screen-shell screen-center"):
            with Vertical(classes="card", id="startup-container"):
                yield Label("Telegram TUI Client", id="login-title")
                yield LoadingIndicator()
                yield Static(self.message, classes="setup-copy", id="startup-message")
        yield Footer()

    def update_message(self, message: str) -> None:
        self.message = message
        try:
            self.query_one("#startup-message", Static).update(message)
        except NoMatches:
            pass
