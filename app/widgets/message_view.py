from __future__ import annotations

from typing import Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static
from textual.widget import Widget

from app.client import TelegramService
from app.utils.formatting import (
    format_message_entities,
    format_sender_name,
    format_timestamp,
    safe_chat_name,
)


class MessageBubble(Static):
    """Renderable message bubble in the scroll area."""

    def __init__(self, message: object) -> None:
        super().__init__(self._build_renderable(message))
        self.message = message
        self.message_id = getattr(message, "id", None)
        self.add_class("message-outgoing" if getattr(message, "out", False) else "message-incoming")

    def update_message(self, message: object) -> None:
        self.message = message
        self.update(self._build_renderable(message))

    @staticmethod
    def _build_renderable(message: object) -> Text:
        content = Text()

        if not getattr(message, "out", False):
            content.append(f"{format_sender_name(message)}\n", style="bold #1d4ed8")

        content.append_text(format_message_entities(message))

        meta_parts = []
        if getattr(message, "edit_date", None) is not None:
            meta_parts.append("edited")

        timestamp = format_timestamp(getattr(message, "date", None))
        if timestamp:
            meta_parts.append(timestamp)

        if meta_parts:
            content.append("\n")
            content.append(" | ".join(meta_parts), style="dim")

        return content


class MessageView(Widget):
    """Main message list and header."""

    def __init__(self, service: TelegramService) -> None:
        super().__init__()
        self.service = service
        self.current_dialog = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Select a chat to begin.", id="message-header")
            yield VerticalScroll(id="message-scroll")

    async def load_messages(self, dialog: object) -> None:
        self.current_dialog = dialog
        entity = getattr(dialog, "entity", None)
        header = self.query_one("#message-header", Static)
        header.update(safe_chat_name(entity))

        scroll = self.query_one("#message-scroll", VerticalScroll)
        await scroll.remove_children()

        try:
            messages = await self.service.get_messages(entity, limit=50)
        except Exception as exc:
            await scroll.mount(Static(f"Failed to load messages: {exc}", classes="placeholder"))
            return

        if not messages:
            await scroll.mount(Static("No messages yet.", classes="placeholder"))
            return

        for message in messages:
            await scroll.mount(MessageBubble(message))

        scroll.scroll_end(animate=False)

    async def add_message(self, message: object) -> None:
        if not self._belongs_to_current_chat(message):
            return

        scroll = self.query_one("#message-scroll", VerticalScroll)
        if self._find_message_bubble(getattr(message, "id", None)) is not None:
            return
        if self._has_placeholder(scroll):
            await scroll.remove_children()

        await scroll.mount(MessageBubble(message))
        scroll.scroll_end(animate=False)

    async def upsert_message(self, message: object) -> None:
        if not self._belongs_to_current_chat(message):
            return

        bubble = self._find_message_bubble(getattr(message, "id", None))
        if bubble is None:
            await self.add_message(message)
            return

        bubble.update_message(message)

    async def remove_messages(self, deleted_ids: list[int]) -> None:
        scroll = self.query_one("#message-scroll", VerticalScroll)
        removed = False

        for child in list(scroll.children):
            if isinstance(child, MessageBubble) and child.message_id in deleted_ids:
                await child.remove()
                removed = True

        if removed and not scroll.children:
            await scroll.mount(Static("No messages yet.", classes="placeholder"))

    def _find_message_bubble(self, message_id: object) -> Optional[MessageBubble]:
        scroll = self.query_one("#message-scroll", VerticalScroll)
        for child in scroll.children:
            if isinstance(child, MessageBubble) and child.message_id == message_id:
                return child
        return None

    def _belongs_to_current_chat(self, message: object) -> bool:
        if self.current_dialog is None:
            return False
        return getattr(self.current_dialog, "id", None) == getattr(message, "chat_id", None)

    @staticmethod
    def _has_placeholder(scroll: VerticalScroll) -> bool:
        return any(isinstance(child, Static) and "placeholder" in child.classes for child in scroll.children)
