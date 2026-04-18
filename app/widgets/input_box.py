from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input

from app.client import TelegramService


class InputBox(Widget):
    """Message composer."""

    class MessageSent(Message):
        def __init__(self, message: object) -> None:
            super().__init__()
            self.message = message

    def __init__(self, service: TelegramService) -> None:
        super().__init__()
        self.service = service
        self.current_dialog = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="input-container"):
            yield Button("Attach", id="attach-btn")
            yield Button("Emoji", id="emoji-btn")
            yield Input(placeholder="Type a message...", id="message-input")
            yield Button("Send", id="send-btn", variant="primary")

    def set_chat(self, dialog: object) -> None:
        self.current_dialog = dialog

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            await self.send_message()
        elif event.button.id == "attach-btn":
            self.app.notify("Attachment flow is not implemented yet.", title="Telegram TUI")
        elif event.button.id == "emoji-btn":
            self.app.notify("Emoji picker is not implemented yet.", title="Telegram TUI")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "message-input":
            await self.send_message()

    async def send_message(self) -> None:
        if self.current_dialog is None:
            self.app.notify("Select a chat before sending a message.", title="Telegram TUI")
            return

        input_widget = self.query_one("#message-input", Input)
        text = input_widget.value.strip()
        if not text:
            return

        try:
            message = await self.service.send_message(
                getattr(self.current_dialog, "entity", None),
                text,
            )
        except Exception as exc:
            self.app.notify(f"Failed to send message: {exc}", severity="error")
            return

        input_widget.value = ""
        self.post_message(self.MessageSent(message))

    def focus_input(self) -> None:
        self.query_one("#message-input", Input).focus()
