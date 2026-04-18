from __future__ import annotations

from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label, ListItem, ListView, Static

from app.client import TelegramService
from app.utils.formatting import format_timestamp, safe_chat_name, safe_message_preview


class ChatListItem(ListItem):
    """Single entry in the chat list."""

    def __init__(self, dialog: object) -> None:
        super().__init__(classes="chat-item")
        self.dialog = dialog

    def compose(self) -> ComposeResult:
        message = getattr(self.dialog, "message", None)
        unread = getattr(self.dialog, "unread_count", 0) or 0
        meta_parts = []

        timestamp = format_timestamp(getattr(message, "date", None))
        if timestamp:
            meta_parts.append(timestamp)
        if unread:
            meta_parts.append(f"{unread} unread")

        yield Label(safe_chat_name(getattr(self.dialog, "entity", None)), classes="chat-name")
        yield Label(safe_message_preview(message), classes="chat-preview")
        yield Label(" | ".join(meta_parts) if meta_parts else " ", classes="chat-meta")


class ChatList(Widget):
    """Sidebar with dialog search and selection."""

    class ChatSelected(Message):
        def __init__(self, dialog: object) -> None:
            super().__init__()
            self.dialog = dialog

    def __init__(self, service: TelegramService) -> None:
        super().__init__()
        self.service = service
        self.dialogs: List[object] = []
        self.selected_dialog_id: Optional[int] = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Input(placeholder="Search chats", id="search-input")
            yield ListView(id="chat-list-view")

    async def on_mount(self) -> None:
        await self.reload()

    async def reload(self) -> None:
        try:
            self.dialogs = await self.service.get_dialogs(limit=100)
        except Exception as exc:
            self.dialogs = []
            list_view = self.query_one("#chat-list-view", ListView)
            await list_view.remove_children()
            list_view.append(
                ListItem(Static(f"Failed to load chats: {exc}", classes="placeholder"))
            )
            return

        await self._render_dialogs(self.dialogs)

    async def _render_dialogs(self, dialogs: List[object]) -> None:
        list_view = self.query_one("#chat-list-view", ListView)
        await list_view.remove_children()

        if not dialogs:
            list_view.append(ListItem(Static("No chats found.", classes="placeholder")))
            return

        for dialog in dialogs:
            list_view.append(ChatListItem(dialog))

        selected_index = 0
        if self.selected_dialog_id is not None:
            for index, dialog in enumerate(dialogs):
                if getattr(dialog, "id", None) == self.selected_dialog_id:
                    selected_index = index
                    break

        list_view.index = selected_index

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search-input":
            return

        query = event.value.strip().lower()
        if not query:
            await self._render_dialogs(self.dialogs)
            return

        filtered = [
            dialog
            for dialog in self.dialogs
            if query in safe_chat_name(getattr(dialog, "entity", None)).lower()
            or query in safe_message_preview(getattr(dialog, "message", None)).lower()
        ]
        await self._render_dialogs(filtered)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if not isinstance(event.item, ChatListItem):
            return

        self.selected_dialog_id = getattr(event.item.dialog, "id", None)
        self.post_message(self.ChatSelected(event.item.dialog))

    def focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()
