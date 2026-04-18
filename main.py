import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.tui import TelegramTUI


def main() -> None:
    """Run the Telegram TUI application."""
    TelegramTUI().run()


if __name__ == "__main__":
    main()
