from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from app.client import (
    MessageDeletedEvent,
    MessageEditedEvent,
    NewMessageEvent,
    TelegramService,
)
from app.utils.formatting import safe_chat_name
from app.widgets.chat_list import ChatList
from app.widgets.input_box import InputBox
from app.widgets.message_view import MessageView


class MainScreen(Screen[None]):
    """Primary chat layout."""

    def __init__(self, service: TelegramService) -> None:
        super().__init__()
        self.service = service
        self.current_dialog = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-shell"):
            with Vertical(id="sidebar"):
                yield ChatList(self.service)
            with Vertical(id="center-pane"):
                yield MessageView(self.service)
                yield InputBox(self.service)
            with Vertical(id="info-panel", classes="hidden"):
                yield Static("Select a chat to see details.", id="info-content")
        yield Footer()

    async def on_chat_list_chat_selected(self, event: ChatList.ChatSelected) -> None:
        self.current_dialog = event.dialog
        await self.query_one(MessageView).load_messages(event.dialog)
        self.query_one(InputBox).set_chat(event.dialog)
        self._update_info_panel(event.dialog)

    async def on_input_box_message_sent(self, event: InputBox.MessageSent) -> None:
        await self.query_one(MessageView).add_message(event.message)

    async def handle_client_event(self, event: object) -> None:
        chat_list = self.query_one(ChatList)
        message_view = self.query_one(MessageView)

        if isinstance(event, NewMessageEvent):
            if self._is_current_chat(event.chat_id):
                await message_view.add_message(event.message)
            await chat_list.reload()
            return

        if isinstance(event, MessageEditedEvent):
            if self._is_current_chat(event.chat_id):
                await message_view.upsert_message(event.message)
            await chat_list.reload()
            return

        if isinstance(event, MessageDeletedEvent):
            if self._is_current_chat(event.chat_id):
                await message_view.remove_messages(event.deleted_ids)
            await chat_list.reload()

    def toggle_sidebar(self) -> None:
        self.query_one("#sidebar").toggle_class("hidden")

    def toggle_info_panel(self) -> None:
        self.query_one("#info-panel").toggle_class("hidden")

    def focus_search(self) -> None:
        self.query_one(ChatList).focus_search()

    def show_help(self) -> None:
        self.app.notify(
            "Shortcuts: Ctrl+Q quit, Ctrl+S sidebar, Ctrl+I info, Ctrl+F search.",
            title="Telegram TUI",
        )

    def _update_info_panel(self, dialog: object) -> None:
        entity = getattr(dialog, "entity", None)
        info_lines = [
            safe_chat_name(entity),
            "",
            f"Unread: {getattr(dialog, 'unread_count', 0)}",
            f"Dialog ID: {getattr(dialog, 'id', 'n/a')}",
        ]
        self.query_one("#info-content", Static).update("\n".join(info_lines))

    def _is_current_chat(self, chat_id: object) -> bool:
        if self.current_dialog is None:
            return False
        return getattr(self.current_dialog, "id", None) == chat_id
