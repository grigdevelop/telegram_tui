from app.utils.formatting import safe_message_preview


class DummyMessage:
    def __init__(self, message: str) -> None:
        self.message = message
        self.raw_text = message
        self.media = None


def test_safe_message_preview_truncates_long_text() -> None:
    message = DummyMessage("x" * 60)
    assert safe_message_preview(message, width=20) == "xxxxxxxxxxxxxxxxx..."
