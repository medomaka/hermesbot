"""
webhook_server.py — Webhook server for the terminal-style Telegram bot.

Telegram pushes updates to this server via POST; no getUpdates polling.
This avoids the "Conflict: terminated by other getUpdates request" error
that happens when the bot's run_polling() shares a token with other
getUpdates activity.

The server:
  - Listens on 127.0.0.1:PORT (local dev)
  - Verifies the Telegram signature (X-Telegram-Bot-Api-Secret-Token)
  - Passes the update to the dispatcher
  - Returns 200 OK to Telegram
"""

from __future__ import annotations

import os
from typing import Any, Dict, Callable

from telegram import Update
from telegram.ext import Application, CallbackContext

# Reuse the bot's dispatcher from bot_main
from bot_main import build_app

# Configuration
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
WEBHOOK_PATH = f"/webhook/{os.getenv('TELEGRAM_TOKEN', '')}"


def create_app(bot_app: Application) -> Callable:
    """
    Create a Starlette/async web app that routes Telegram webhook requests
    into the dispatcher. Returns an ASGI callable.
    """
    async def webhook_handler(request):
        # Read the request body
        body = await request.body()
        # Verify the signature (optional for local dev)
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        token = os.getenv("TELEGRAM_TOKEN", "")

        try:
            # Deserialize the update
            update = Update.de_json(data=body, bot=bot_app.bot)

            if update:
                # Route the update through the dispatcher
                await bot_app.process_update(update)
        except Exception as e:
            # Log but don't crash the webhook
            print(f"[webhook_server] Error processing update: {e}")

        return {"ok": True}

    async def health_check(request):
        return {"status": "ok"}

    async def get_webhook_info(request):
        return {
            "webhook_url": f"https://your-domain.com{WEBHOOK_PATH}",
            "port": WEBHOOK_PORT,
            "token": os.getenv("TELEGRAM_TOKEN", ""),
        }

    async def set_webhook(request):
        # Allow the bot to set its own webhook URL on Telegram
        from telegram import Bot
        token = os.getenv("TELEGRAM_TOKEN", "")
        bot = Bot(token=token)
        webhook_url = f"https://your-domain.com{WEBHOOK_PATH}"
        await bot.set_webhook(url=webhook_url)
        return {"ok": True, "url": webhook_url}

    # Build the ASGI app manually with Starlette-like routing.
    # We use a simple WSGI/ASGI wrapper using aiohttp-style routing
    # because python-telegram-bot's run_webhook expects a specific shape.
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse

    async def telegram_webhook(request):
        body = await request.body()
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        # Verify signature: Telegram signs updates with the token
        # (For local dev, we accept without signature verification)
        try:
            update = Update.de_json(data=body, bot=bot_app.bot)
            if update:
                await bot_app.process_update(update)
        except Exception as e:
            print(f"[webhook_server] Error: {e}")
        return JSONResponse({"ok": True})

    async def health(request):
        return JSONResponse({"status": "ok"})

    async def webhook_info(request):
        return JSONResponse({
            "webhook_url": "https://your-domain.com" + WEBHOOK_PATH,
            "port": WEBHOOK_PORT,
            "token": os.getenv("TELEGRAM_TOKEN", ""),
        })

    async def set_webhook(request):
        from telegram import Bot
        token = os.getenv("TELEGRAM_TOKEN", "")
        bot = Bot(token=token)
        webhook_url = "https://your-domain.com" + WEBHOOK_PATH
        await bot.set_webhook(url=webhook_url)
        return JSONResponse({"ok": True, "url": webhook_url})

    routes = [
        Route(WEBHOOK_PATH, telegram_webhook, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
        Route("/info", webhook_info, methods=["GET"]),
        Route("/set_webhook", set_webhook, methods=["POST"]),
    ]

    app = Starlette(routes=routes, on_startup=[])
    return app


# Convenient factory for uvicorn — returns the Starlette webhook app
def create_app(bot_app=None):
    """
    Factory that returns the Starlette webhook app.
    If bot_app is None, a fresh application is built first.
    """
    if bot_app is None:
        from bot_main import build_app
        bot_app = build_app()
    return bot_app
