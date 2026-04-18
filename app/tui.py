from __future__ import annotations

import asyncio
import logging
import traceback
from pathlib import Path

_LOG_PATH = Path(__file__).resolve().parents[1] / "tui_debug.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler(_LOG_PATH, mode="a", encoding="utf-8")],
    force=True,
)
logging.getLogger("telethon").setLevel(logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.DEBUG)

from textual.app import App
from textual.binding import Binding

from app.client import TelegramService
from app.screens.login_screen import LoginScreen
from app.screens.main_screen import MainScreen
from app.screens.startup_screen import StartupScreen
from app.screens.setup_screen import SetupScreen
from app.utils.config import Config


class TelegramTUI(App[None]):
    """Main Textual application for the Telegram client."""

    CSS_PATH = Path(__file__).with_name("styles.tcss")
    TITLE = "Telegram TUI Client"
    CONNECT_TIMEOUT_SECONDS = 60
    AUTH_TIMEOUT_SECONDS = 30

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+s", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+i", "toggle_info", "Info"),
        Binding("ctrl+f", "search", "Search"),
        Binding("ctrl+n", "new_chat", "New Chat"),
        Binding("f1", "help", "Help"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = Config()
        self.service = TelegramService(self.config)

    async def on_mount(self) -> None:
        self.push_screen(StartupScreen("Starting Telegram TUI..."))
        self.run_worker(self._bootstrap(), exclusive=True)

    async def _bootstrap(self) -> None:
        if not self.service.available:
            await self.show_setup_screen()
            return

        # Textual enables asyncio.eager_task_factory on the running loop, which
        # causes telethon's send/receive loop tasks to run before
        # `_user_connected` is set, exiting immediately and deadlocking every
        # subsequent request. Restore the default factory for this loop.
        asyncio.get_running_loop().set_task_factory(None)

        self.update_startup_message("Connecting to Telegram...")
        try:
            await asyncio.wait_for(
                self.service.connect(),
                timeout=self.CONNECT_TIMEOUT_SECONDS,
            )
        except (TimeoutError, asyncio.TimeoutError):
            self._write_debug_log("connect timeout", "TimeoutError from asyncio.wait_for")
            await self.show_setup_screen(
                details=(
                    "Connection timed out after "
                    f"{self.CONNECT_TIMEOUT_SECONDS} seconds during client.connect(). "
                    f"Session path: {self.config.session_path}. "
                    f"API ID set: {bool(self.config.api_id)}, API hash set: {bool(self.config.api_hash)}. "
                    "See tui_debug.log for details."
                )
            )
            return
        except Exception as exc:
            tb = traceback.format_exc()
            self._write_debug_log("connect exception", tb)
            await self.show_setup_screen(
                details=f"Connection failed: {type(exc).__name__}: {exc}\n\n{tb}"
            )
            return

        self.run_worker(self._forward_client_events())

        self.update_startup_message("Checking Telegram session...")
        try:
            is_authorized = await asyncio.wait_for(
                self.service.is_authorized(),
                timeout=self.AUTH_TIMEOUT_SECONDS,
            )
        except (TimeoutError, asyncio.TimeoutError):
            await self.show_setup_screen(
                details=(
                    "Session check timed out after "
                    f"{self.AUTH_TIMEOUT_SECONDS} seconds. "
                    "Your session may be stale, or Telegram may be unreachable."
                )
            )
            return
        except Exception as exc:
            tb = traceback.format_exc()
            await self.show_setup_screen(
                details=f"Session check failed: {type(exc).__name__}: {exc}\n\n{tb}"
            )
            return

        if is_authorized:
            self.update_startup_message("Loading chats...")
            await self.show_main_screen()
        else:
            self.update_startup_message("Opening login screen...")
            await self.show_login_screen()

    async def _forward_client_events(self) -> None:
        while True:
            event = await self.service.next_ui_event()
            if isinstance(self.screen, MainScreen):
                await self.screen.handle_client_event(event)

    async def show_main_screen(self) -> None:
        if isinstance(self.screen, MainScreen):
            return

        if isinstance(self.screen, (LoginScreen, SetupScreen, StartupScreen)):
            self.pop_screen()

        self.push_screen(MainScreen(self.service))

    async def show_login_screen(self) -> None:
        if isinstance(self.screen, LoginScreen):
            return

        if isinstance(self.screen, (SetupScreen, StartupScreen)):
            self.pop_screen()

        self.push_screen(LoginScreen(self.service))

    async def show_setup_screen(self, details: str = "") -> None:
        if isinstance(self.screen, SetupScreen):
            self.pop_screen()

        if isinstance(self.screen, (LoginScreen, StartupScreen)):
            self.pop_screen()

        self.push_screen(SetupScreen(self.config, details=details))

    def _write_debug_log(self, tag: str, body: str) -> None:
        try:
            log_path = Path(__file__).resolve().parents[1] / "tui_debug.log"
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(f"--- {tag} ---\n{body}\n\n")
        except Exception:
            pass

    def update_startup_message(self, message: str) -> None:
        if isinstance(self.screen, StartupScreen):
            self.screen.update_message(message)

    async def action_quit(self) -> None:
        await self.service.disconnect()
        self.exit()

    def action_toggle_sidebar(self) -> None:
        if isinstance(self.screen, MainScreen):
            self.screen.toggle_sidebar()

    def action_toggle_info(self) -> None:
        if isinstance(self.screen, MainScreen):
            self.screen.toggle_info_panel()

    def action_search(self) -> None:
        if isinstance(self.screen, MainScreen):
            self.screen.focus_search()

    def action_new_chat(self) -> None:
        self.notify("New chat flow is not implemented yet.", title="Telegram TUI")

    def action_help(self) -> None:
        if isinstance(self.screen, MainScreen):
            self.screen.show_help()
        else:
            self.notify("Configure credentials, sign in, then use the main screen shortcuts.")

    def action_cancel(self) -> None:
        if isinstance(self.screen, MainScreen):
            return
        self.exit()
