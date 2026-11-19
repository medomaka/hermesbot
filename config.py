"""
config.py — Configuration for the terminal-style Telegram bot.

Copy this file into your project and set TELEGRAM_TOKEN.
"""

import os

# --- Telegram ---
# Your bot token. In production, set TELEGRAM_TOKEN as an environment
# variable instead of hardcoding it.
TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN",
    "9097468849:AAEqg3_toi3jijmbDOiCfOtBDHPv6KWAVSY",
)

# Webhook (for hosting) vs long-polling (local dev)
USE_WEBHOOK = False

# Port for the webhook server (for local webhook mode)
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))

# Public HTTPS URL for webhook delivery (Render app URL)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://hermesbot-589t.onrender.com/webhook/9097468849_*")

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

# --- Dashboard assets ---
DASHBOARD_VARS = {
    "session": "001",
    "uptime": "0",
    "cmd": "0",
    "clients": "0",
    "theme": "solar",
}
