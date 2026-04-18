from __future__ import annotations

from typing import TYPE_CHECKING

from telethon.errors import SessionPasswordNeededError
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from app.client import TelegramService

if TYPE_CHECKING:
    from app.tui import TelegramTUI


class LoginScreen(Screen[None]):
    """Telegram sign-in flow."""

    def __init__(self, service: TelegramService) -> None:
        super().__init__()
        self.service = service
        self.phone_number = ""

    @property
    def app(self) -> "TelegramTUI":
        return super().app

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="screen-shell screen-center"):
            with Vertical(classes="card", id="login-container"):
                yield Label("Telegram Sign In", id="login-title")
                yield Static("Enter your phone number with country code.")
                yield Input(placeholder="+1234567890", id="phone-input")
                yield Button("Send Code", id="send-code", variant="primary")
                yield Input(placeholder="Verification code", id="code-input", disabled=True)
                yield Button("Verify Code", id="verify-code", disabled=True)
                yield Input(
                    placeholder="Two-factor password",
                    password=True,
                    id="password-input",
                    disabled=True,
                )
                yield Button("Submit Password", id="submit-password", disabled=True)
                yield Static("", id="login-status")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-code":
            await self._send_code()
        elif event.button.id == "verify-code":
            await self._verify_code()
        elif event.button.id == "submit-password":
            await self._submit_password()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "phone-input":
            await self._send_code()
        elif event.input.id == "code-input":
            await self._verify_code()
        elif event.input.id == "password-input":
            await self._submit_password()

    async def _send_code(self) -> None:
        phone_input = self.query_one("#phone-input", Input)
        self.phone_number = phone_input.value.strip()

        if not self.phone_number:
            self._set_status("Enter a phone number first.")
            return

        try:
            await self.service.request_login_code(self.phone_number)
        except Exception as exc:
            self._set_status(f"Failed to request code: {exc}")
            return

        self.query_one("#code-input", Input).disabled = False
        self.query_one("#verify-code", Button).disabled = False
        self._set_status("Code sent. Check Telegram and enter it here.")

    async def _verify_code(self) -> None:
        code_input = self.query_one("#code-input", Input)
        code = code_input.value.strip()

        if not code:
            self._set_status("Enter the verification code first.")
            return

        try:
            await self.service.sign_in_code(self.phone_number, code)
        except SessionPasswordNeededError:
            self.query_one("#password-input", Input).disabled = False
            self.query_one("#submit-password", Button).disabled = False
            self._set_status("Two-factor authentication is enabled. Enter your password.")
            return
        except Exception as exc:
            self._set_status(f"Sign-in failed: {exc}")
            return

        self._set_status("Login successful. Loading chats...")
        await self.app.show_main_screen()

    async def _submit_password(self) -> None:
        password_input = self.query_one("#password-input", Input)
        password = password_input.value.strip()

        if not password:
            self._set_status("Enter your two-factor password.")
            return

        try:
            await self.service.sign_in_password(password)
        except Exception as exc:
            self._set_status(f"Password sign-in failed: {exc}")
            return

        self._set_status("Login successful. Loading chats...")
        await self.app.show_main_screen()

    def _set_status(self, message: str) -> None:
        self.query_one("#login-status", Static).update(message)
