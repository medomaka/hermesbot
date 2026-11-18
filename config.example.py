"""
config.example.py — Configuration for the terminal-style Telegram bot.

Copy to config.py and fill in your bot token.
"""

import os

# --- Telegram ---
# Your Hermes-bot token (or a standalone python-telegram-bot token)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Webhook (for hosting) vs long-polling (local dev)
USE_WEBHOOK = False

# Bot name displayed in the terminal dashboard
BOT_NAME = "Terminal Bot"
BOT_VERSION = "1.0.0"

# --- Live calls ---
# "telegram" (group voice chat MVP) or "webrtc" (1:1 relay)
LIVE_CALL_TRANSPORT = "telegram"

# For webrtc: the signaling relay base URL
WEBRTC_SIGNAL_URL = os.getenv("WEBRTC_SIGNAL_URL", "ws://localhost:8765")

# --- Themes ---
DEFAULT_THEME = "solar"  # terminal | midnight | ocean | solar

# --- Dashboard assets (session, uptime, etc.) ----
# Override in a derivatives class, or in config.py as a dict.
DASHBOARD_VARS = {
    "session": "001",
    "uptime": "0",
    "cmd": "0",
    "clients": "0",
    "theme": "solar",
}
