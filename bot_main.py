"""
bot_main.py — Entry point for the terminal-style Telegram bot.

Wires the dispatcher: command router, message handler, callback handler,
and the rich message renderer (theme + dashboard + apps).

Usage:
    # run via Hermes host
    python bot_main.py

The bot token is read from config.py (or env TELEGRAM_TOKEN).
"""

from __future__ import annotations

import os
import sys

# Ensure the package root is on sys.path so absolute imports work.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# Bot configuration (token, webhook port, etc.)
from config import TELEGRAM_TOKEN, WEBHOOK_PORT, WEBHOOK_URL

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_TOKEN
from router import router
from dashboard import dash, Dashboard
from apps import apps
from call import CallState, transport_factory
from renderer import render_blocks, render_blocks as _render_blocks
from theme import get_theme

# ---- call state (single-room MVP) ----
calls = CallState(active=False)
call_transport = None


# ---- Command handlers ----
@router.command("start", help_text="/start — start the bot and show the dashboard")
async def cmd_start(context: dict) -> str:
    msg = context.get("message")
    if msg:
        await msg.reply_text(
            "Terminal Dashboard",
            reply_markup=dash.build()["keyboard"],
            parse_mode="MarkdownV2",
        )
    return "ok"


@router.command("help", help_text="/help — show the command palette")
async def cmd_help(context: dict) -> str:
    msg = context.get("message")
    if msg:
        blocks = [
            {"type": "header", "title": "Command Palette", "subtitle": ""},
            {"type": "code", "lang": "commands",
             "content": "\n".join(sorted(router.commands))},
            {"type": "text", "content": "tap ▸ to open a panel · /theme [name] to switch theme"},
        ]
        body, extras = render_blocks(blocks)
        await msg.reply_text(body, reply_markup=extras["keyboard"],
                             parse_mode="MarkdownV2")
    return "ok"


@router.command("theme", help_text="/theme [name] — switch terminal theme")
async def cmd_theme(context: dict) -> str:
    msg = context.get("message")
    args = context.get("args", [])
    if args:
        name = args[0].lower()
        try:
            from theme import set_theme, list_themes
            set_theme(name)
            info = f"Theme switched to `{name}`. Available: {list_themes()}"
        except KeyError as e:
            info = f"Unknown theme: {e}; available: {list_themes()}"
    else:
        from theme import get_theme, list_themes
        info = f"Current theme: `{get_theme().name}`. Available: {list_themes()}"
    if msg:
        await msg.reply_text(info, parse_mode="MarkdownV2")
    return "ok"


@router.command("stats", help_text="/stats — show live system stats")
async def cmd_stats(context: dict) -> str:
    msg = context.get("message")
    if msg:
        blocks = [
            {"type": "panel",
             "title": "System Stats",
             "content": f"session `{context.get('extra',{}).get('session','?')}` · "
                        f"uptime `{context.get('extra',{}).get('uptime','?')}` "
                        f"· commands `{context.get('extra',{}).get('cmd','?')}`",
             "footer": "tap ▸ back", "width": 46},
        ]
        body, extras = render_blocks(blocks)
        await msg.reply_text(body, reply_markup=extras["keyboard"],
                             parse_mode="MarkdownV2")
    return "ok"


@router.command("status", help_text="/status — short status line")
async def cmd_status(context: dict) -> str:
    msg = context.get("message")
    if msg:
        body = (
            f"`▣` status: running · "
            f"session `{context.get('extra',{}).get('session','?')}` · "
            f"clients `{context.get('extra',{}).get('clients','?')}`"
        )
        await msg.reply_text(body, parse_mode="MarkdownV2")
    return "ok"


@router.command("clear", help_text="/clear — reset chat context")
async def cmd_clear(context: dict) -> str:
    msg = context.get("message")
    if msg:
        await msg.reply_text("Context cleared.", parse_mode="MarkdownV2")
    return "ok"


# ---- Callback router ----
@router.callback_handler
async def handle_callback(data: dict, context: dict) -> str:
    payload = data.get("payload", "")
    # 'dashboard' / 'theme' are top-level; route:<name> opens panels
    if payload == "dashboard":
        await data["message"].edit_text(
            "Dashboard",
            reply_markup=dash.build()["keyboard"],
            parse_mode="MarkdownV2",
        )
        return "ok"
    if payload == "theme":
        # Simple: re-show theme selector
        from theme import list_themes
        await data["message"].edit_text(
            "Themes: " + ", ".join(list_themes()),
            reply_markup=dash.build()["keyboard"],
            parse_mode="MarkdownV2",
        )
        return "ok"
    if payload.startswith("route:"):
        route = payload.split(":", 1)[1]
        app = apps.get(route)
        if app:
            result = app["renderer"](context)
            blocks = result.get("blocks", [])
            kb = result.get("keyboard")
            new_blocks = [
                {"type": "header", "title": app["title"], "subtitle": ""},
                *blocks,
            ]
            body, extras = render_blocks(new_blocks)
            await data["message"].edit_text(body,
                                            reply_markup=extras["keyboard"],
                                            parse_mode="MarkdownV2")
        else:
            await data["message"].edit_text(
                f"`✖` no app for route `{route}`. /help",
                parse_mode="MarkdownV2")
        return "ok"
    # unknown callback: re-show dashboard
    await data["message"].edit_text(
        "No action. Return to dashboard with /dashboard.",
        parse_mode="MarkdownV2")
    return "ok"


# ---- Message handler (already routed by router, but keep for completeness) ----
async def handle_text(update: Update, context: dict) -> None:
    text = update.message.text or ""
    await router.handle_text(text, context)


# ---- Build the application ----
def build_app() -> Application:
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command handlers - wrap router handlers to match Telegram's signature
    for name, fn in router.commands.items():
        # Router handlers take (context: dict), but Telegram's CommandHandler
        # expects (update, context). Create a wrapper.
        def make_wrapper(handler):
            async def wrapper(update, context):
                return await handler(context)
            return wrapper
        app.add_handler(CommandHandler(name, make_wrapper(fn)))

    # Callback handler
    app.add_handler(CallbackQueryHandler(handle_callback, pattern=".+"))

    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app


if __name__ == "__main__":
    # Start in webhook mode (recommended for Render deployment)
    # Webhooks push updates to your server instead of polling
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command handlers - wrap router handlers to match Telegram's signature
    for name, fn in router.commands.items():
        # Router handlers take (context: dict), but Telegram's CommandHandler
        # expects (update, context). Create a wrapper.
        def make_wrapper(handler):
            async def wrapper(update, context):
                return await handler(context)
            return wrapper
        app.add_handler(CommandHandler(name, make_wrapper(fn)))

    # Callback handler
    app.add_handler(CallbackQueryHandler(handle_callback, pattern=".+"))

    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start in webhook mode (recommended for Render deployment)
    # Webhooks push updates to your server instead of polling
    app.run_webhook(
        listen="0.0.0.0",
        port=WEBHOOK_PORT,
        url_path=f"/webhook/{TELEGRAM_TOKEN.replace(':', '_')}",
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True,
    )
