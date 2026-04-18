from __future__ import annotations

from datetime import datetime
from typing import Optional

from rich.text import Text
from telethon.tl.types import (
    MessageEntityBold,
    MessageEntityCode,
    MessageEntityItalic,
    MessageEntityStrike,
    MessageEntityTextUrl,
    MessageEntityUrl,
)


def safe_chat_name(entity: object) -> str:
    if entity is None:
        return "Unknown Chat"

    title = getattr(entity, "title", None)
    if title:
        return title

    first_name = getattr(entity, "first_name", None) or ""
    last_name = getattr(entity, "last_name", None) or ""
    full_name = f"{first_name} {last_name}".strip()
    if full_name:
        return full_name

    username = getattr(entity, "username", None)
    if username:
        return f"@{username}"

    return "Unknown Chat"


def safe_message_text(message: object) -> str:
    text = getattr(message, "message", None) or getattr(message, "raw_text", None)
    if text:
        return text
    if getattr(message, "media", None) is not None:
        return "[Media]"
    return ""


def safe_message_preview(message: Optional[object], width: int = 48) -> str:
    if message is None:
        return "No messages yet"

    preview = safe_message_text(message).replace("\n", " ").strip() or "No messages yet"
    if len(preview) <= width:
        return preview
    return preview[: width - 3].rstrip() + "..."


def format_timestamp(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    return value.strftime("%H:%M")


def format_sender_name(message: object) -> str:
    if getattr(message, "out", False):
        return "You"

    sender = getattr(message, "sender", None)
    if sender is not None:
        first_name = getattr(sender, "first_name", None) or ""
        last_name = getattr(sender, "last_name", None) or ""
        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            return full_name

    sender_id = getattr(message, "sender_id", None)
    if sender_id is not None:
        return f"User {sender_id}"

    return "Unknown"


def format_message_entities(message: object) -> Text:
    text = Text(safe_message_text(message))
    entities = getattr(message, "entities", None) or []

    for entity in entities:
        start = getattr(entity, "offset", 0)
        end = start + getattr(entity, "length", 0)

        if isinstance(entity, MessageEntityBold):
            text.stylize("bold", start, end)
        elif isinstance(entity, MessageEntityItalic):
            text.stylize("italic", start, end)
        elif isinstance(entity, MessageEntityCode):
            text.stylize("reverse", start, end)
        elif isinstance(entity, MessageEntityStrike):
            text.stylize("strike", start, end)
        elif isinstance(entity, (MessageEntityUrl, MessageEntityTextUrl)):
            text.stylize("underline #2563eb", start, end)

    return text
