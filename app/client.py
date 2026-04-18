from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Optional

from telethon import TelegramClient, events

from app.utils.config import Config


@dataclass
class NewMessageEvent:
    chat_id: Optional[int]
    message: object


@dataclass
class MessageEditedEvent:
    chat_id: Optional[int]
    message: object


@dataclass
class MessageDeletedEvent:
    chat_id: Optional[int]
    deleted_ids: List[int]


class TelegramService:
    """Thin wrapper around Telethon for the Textual UI."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.client: Optional[TelegramClient] = None
        self.ui_events: Optional["asyncio.Queue[object]"] = None

        if not config.has_credentials:
            return

        self.config.ensure_directories()

    @property
    def available(self) -> bool:
        return self.config.has_credentials

    def _ensure_client(self) -> TelegramClient:
        if self.client is None:
            if not self.config.has_credentials:
                raise RuntimeError(
                    "Missing TELEGRAM_API_ID or TELEGRAM_API_HASH. Add them to .env first."
                )
            self.client = TelegramClient(
                str(self.config.session_path),
                self.config.api_id,
                self.config.api_hash,
                device_model="Telegram TUI Client",
                system_version="Textual",
                app_version="0.1.0",
            )
            self.ui_events = asyncio.Queue()
            self._setup_handlers()
        return self.client

    def _require_client(self) -> TelegramClient:
        return self._ensure_client()

    def _setup_handlers(self) -> None:
        client = self._require_client()

        @client.on(events.NewMessage)
        async def _handle_new_message(event: events.NewMessage.Event) -> None:
            await self.ui_events.put(
                NewMessageEvent(chat_id=getattr(event, "chat_id", None), message=event.message)
            )

        @client.on(events.MessageEdited)
        async def _handle_message_edited(event: events.MessageEdited.Event) -> None:
            await self.ui_events.put(
                MessageEditedEvent(
                    chat_id=getattr(event, "chat_id", None),
                    message=event.message,
                )
            )

        @client.on(events.MessageDeleted)
        async def _handle_message_deleted(event: events.MessageDeleted.Event) -> None:
            deleted_ids = list(getattr(event, "deleted_ids", []) or [])
            await self.ui_events.put(
                MessageDeletedEvent(
                    chat_id=getattr(event, "chat_id", None),
                    deleted_ids=deleted_ids,
                )
            )

    async def connect(self) -> None:
        await self._require_client().connect()

    async def disconnect(self) -> None:
        if self.client is not None and self.client.is_connected():
            await self.client.disconnect()

    async def is_authorized(self) -> bool:
        return await self._require_client().is_user_authorized()

    async def request_login_code(self, phone_number: str) -> None:
        await self._require_client().send_code_request(phone_number)

    async def sign_in_code(self, phone_number: str, code: str) -> object:
        return await self._require_client().sign_in(phone=phone_number, code=code)

    async def sign_in_password(self, password: str) -> object:
        return await self._require_client().sign_in(password=password)

    async def get_dialogs(self, limit: int = 100) -> List[object]:
        dialogs: List[object] = []
        client = self._require_client()

        async for dialog in client.iter_dialogs(limit=limit):
            dialogs.append(dialog)

        return dialogs

    async def get_messages(self, entity: object, limit: int = 50) -> List[object]:
        messages: List[object] = []
        client = self._require_client()

        async for message in client.iter_messages(entity, limit=limit):
            if getattr(message, "message", None) or getattr(message, "media", None):
                messages.append(message)

        messages.reverse()
        return messages

    async def send_message(self, entity: object, text: str) -> object:
        return await self._require_client().send_message(entity, text)

    async def search_messages(
        self, entity: object, query: str, limit: int = 50
    ) -> List[object]:
        results: List[object] = []
        client = self._require_client()

        async for message in client.iter_messages(entity, search=query, limit=limit):
            results.append(message)

        results.reverse()
        return results

    async def next_ui_event(self) -> object:
        self._ensure_client()
        assert self.ui_events is not None
        return await self.ui_events.get()
