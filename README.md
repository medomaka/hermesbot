# Terminal Style Telegram Bot

A beautiful, multifunctional Telegram bot with a **terminal-style UI** —
monospace prompts, bordered panels, code blocks, status indicators, and a
custom theme system — backed by a rich media rendering engine, inline
keyboards, a dashboard, and a plugin-style app loader.

## Architecture

```
bot_main.py            # Entry point, dispatcher wiring (python-telegram-bot)
├── theme.py           # Theme registry (terminal/midnight/ocean/solar)
├── renderer.py        # Rich message renderer (blocks -> MarkdownV2)
├── dashboard.py       # Dashboard panel + inline navigation
├── router.py          # Command + callback dispatch layer
├── apps.py            # Plugin-style app/module loader
├── call.py            # Live voice-call module (Telegram-native / WebRTC)
└── config.example.py  # Configuration template
```

## Themes

4 built-in themes, swappable at runtime via the `/theme` command:

| Theme   | Palette        |
|---------|----------------|
| terminal| green/amber    |
| midnight| green/dark     |
| ocean   | blue/cyan      |
| solar   | blue/purple    |

## Quick start

1. Copy `config.example.py` to `config.py` and set `TELEGRAM_TOKEN`.
2. Install dependencies:
   ```
   pip install python-telegram-bot[aiohttp]
   ```
3. Run:
   ```
   python bot_main.py
   ```
4. Send `/start` — the terminal dashboard opens with inline Keyboard buttons.

## Architectural notes

### Router (`router.py`)
- Slash commands: `/start`, `/help`, `/theme`, `/stats`, `/status`, `/clear`
- Inline keyboard callbacks: `route:<name>` opens an app panel
- Default message handler for anything else

### Apps (`apps.py`)
Apps are self-contained renderers registered via `register(name, route, title, renderer)`:
- chat, media, files, calls, stats, settings, help
- New apps are added by implementing a renderer that returns `{blocks, keyboard}`.

### Live calls (`call.py`)
Two paths:
- **Telegram-native**: group voice chat (MVP, no extra infra)
- **WebRTC**: true 1:1 relay via signaling server (requires extra infrastructure)

## Extending

### Add an app
```python
from apps import register
from renderer import build_panel

def my_app_renderer(context):
    return {
        "blocks": [build_panel("My App", "content"), ...],
        "keyboard": None,
    }

register("myapp", "myapp", "My App", my_app_renderer)
```

### Add a command
```python
@router.command("mycmd", help_text="/mycmd — do something")
async def cmd_mycmd(context):
    return "done"
```

## Live voice (1:1)

Telegram's native voice chat is group-scoped. True 1:1 live voice requires a
WebRTC signaling relay (WebSocket + TURN). See `call.py` for the transport
interface and the full flow.

## Notes

- This is a framework you can drop into your existing Telegram bot. The
  dispatcher and renderer are framework-agnostic; `bot_main.py` shows the
  python-telegram-bot wiring. Swap in your own lib as needed.
