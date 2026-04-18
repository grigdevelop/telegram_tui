# Telegram TUI Client

Terminal-based Telegram client built with Textual and Telethon.

This repository currently contains an early working scaffold:
- startup, setup, and login screens
- dialog list
- message view
- message sending
- live message/update forwarding from Telethon to the UI
- startup diagnostics written to `tui_debug.log`

## Requirements

- Windows, macOS, or Linux terminal with Python 3.12+ recommended
- Telegram API credentials from `https://my.telegram.org/apps`

## Installation

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Current dependencies are:
- `textual`
- `telethon`
- `cryptg`
- `python-dotenv`
- `aiofiles`

## Configuration

Create a `.env` file in the project root:

```env
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_api_hash_here
```

Session files are stored in:

```text
session/
```

Downloaded media is intended to go in:

```text
downloads/
```

## Running

Start the application:

```bash
python main.py
```

Startup flow:
1. `StartupScreen` appears immediately.
2. The app attempts to connect to Telegram.
3. If credentials are missing or connection fails, `SetupScreen` is shown with error details.
4. If the session is not authorized, `LoginScreen` is shown.
5. If the session is already authorized, `MainScreen` opens.

## Login Flow

On first run:
1. Enter your phone number with country code.
2. Request a verification code.
3. Enter the code from Telegram.
4. If your account uses 2FA, enter the password.

## Features Implemented

- Textual-based multi-screen app shell
- Telegram service wrapper around Telethon
- chat list with local search filter
- message history loading
- message composer and send action
- real-time handling for:
  - new messages
  - edited messages
  - deleted messages
- sidebar toggle
- info panel toggle
- startup timeout/error handling

## Keyboard Shortcuts

- `Ctrl+Q`: quit
- `Ctrl+S`: toggle sidebar
- `Ctrl+I`: toggle info panel
- `Ctrl+F`: focus chat search
- `Ctrl+N`: placeholder for new chat
- `F1`: help
- `Esc`: cancel or exit from non-main screens

## Project Structure

```text
main.py
app/
  client.py
  tui.py
  styles.tcss
  screens/
    startup_screen.py
    setup_screen.py
    login_screen.py
    main_screen.py
  widgets/
    chat_list.py
    message_view.py
    input_box.py
  utils/
    config.py
    formatting.py
tests/
```

## Troubleshooting

### Blank or stuck startup

The app writes debug information to:

```text
tui_debug.log
```

If startup fails, check:
- `.env` contains valid `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`
- your network or firewall is not blocking Telegram
- the session file is not stale or corrupted:
  - `session/telegram_session.session`

If needed, remove the session file and sign in again.

### `python` command problems on Windows

If `python` points to the Microsoft Store shim instead of a real interpreter, open a new terminal after installing Python and run:

```bash
python --version
```

## Current Limitations

This is not a full Telegram client yet. The following are still missing or partial:
- attachments
- emoji picker
- new chat flow
- rich conversation search UI
- media download UI
- profile/details panel beyond basic metadata
- better connection recovery and retry controls
- comprehensive tests

## Development

Quick syntax check:

```bash
python -m compileall main.py app tests
```

Basic test file currently included:

```bash
tests/test_formatting.py
```
