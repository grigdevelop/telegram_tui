from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Load environment variables and define important app paths."""

    def __init__(self) -> None:
        self.root_dir = Path(__file__).resolve().parents[2]
        self.env_path = self.root_dir / ".env"
        load_dotenv(self.env_path)

        self.api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
        self.session_dir = self.root_dir / "session"
        self.download_dir = self.root_dir / "downloads"
        self.session_name = "telegram_session"

    @property
    def has_credentials(self) -> bool:
        return self.api_id > 0 and bool(self.api_hash)

    @property
    def session_path(self) -> Path:
        return self.session_dir / self.session_name

    def ensure_directories(self) -> None:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)
