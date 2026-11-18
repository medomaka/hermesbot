"""
apps.py — Plugin-style "app" module loader.

Apps are self-contained panels that plug into the dashboard. Each app
registers:
  - a route (e.g. "chat", "media")
  - a panel renderer (blocks + optional keyboard)
  - optional actions (commands, callbacks)

Apps are loaded via the "apps" registry; new apps can be added without
touching the core bot. They expose a clean hook contract:
    entries = {}          # name -> {route, title, renderer, actions}
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

Handler = Callable[..., Awaitable[Any]]

# Global registry of loaded apps
apps: Dict[str, Dict[str, Any]] = {}


def register(
    name: str,
    route: str,
    title: str,
    renderer: Callable[..., Dict[str, Any]],
    actions: Dict[str, Handler] | None = None,
    callbacks: Dict[str, Handler] | None = None,
) -> None:
    """Register a new app module.

    Each app gets a route (used in inline keyboard and command), a title,
    a renderer function that returns {blocks, keyboard}, and optional
    action/callback handlers.
    """
    if name in apps:
        raise ValueError(f"App '{name}' is already registered.")
    apps[name] = {
        "route": route,
        "title": title,
        "renderer": renderer,
        "actions": actions or {},
        "callbacks": callbacks or {},
    }


def get(name: str) -> Dict[str, Any]:
    if name not in apps:
        raise KeyError(f"App '{name}' not found. Available: {list(apps)}")
    return apps[name]


def list_apps() -> list[str]:
    return list(apps)


def load_builtin_apps() -> None:
    """Register the default app modules."""
    # ---- Chat app ----
    def render_chat(context: Dict[str, Any]) -> Dict[str, Any]:
        import asyncio
        from .renderer import render_blocks, build_prompt

        msg_id = context.get("message_id")
        user = context.get("from", {}).get("username", "user")
        text = context.get("text", "")

        return {
            "blocks": [
                {"type": "header", "title": "Assistant Chat", "subtitle": "live AI assistant"},
                {"type": "prompt", "user": user, "command": text or "/help"},
            ],
            "keyboard": None,
        }

    register("chat", "chat", "Assistant Chat", render_chat)

    # ---- Media app ----
    def render_media(context: Dict[str, Any]) -> Dict[str, Any]:
        from renderer import build_panel

        return {
            "blocks": [
                build_panel(
                    title="Media Studio",
                    content="upload or generate images/video · rich media tools",
                    footer="tap ▸ back",
                    width=46,
                )
            ],
            "keyboard": None,
        }

    register("media", "media", "Media Studio", render_media)

    # ---- Files app ----
    def render_files(context: Dict[str, Any]) -> Dict[str, Any]:
        from renderer import build_panel

        return {
            "blocks": [
                build_panel(
                    title="File Manager",
                    content="browse, upload & manage files",
                    footer="tap ▸ back",
                    width=46,
                )
            ],
            "keyboard": None,
        }

    register("files", "files", "File Manager", render_files)

    # ---- Calls app ----
    def render_calls(context: Dict[str, Any]) -> Dict[str, Any]:
        from renderer import build_panel

        return {
            "blocks": [
                build_panel(
                    title="Live Calls",
                    content="voice-call the bot · inbound/outbound call routing",
                    footer="tap ▸ back",
                    width=46,
                )
            ],
            "keyboard": None,
        }

    register("calls", "calls", "Live Calls", render_calls)

    # ---- Stats app ----
    def render_stats(context: Dict[str, Any]) -> Dict[str, Any]:
        from renderer import build_panel

        ctx = context.get("extra", {})
        return {
            "blocks": [
                build_panel(
                    title="System Stats",
                    content=(
                        f"session `{ctx.get('session','?')}` · uptime `{ctx.get('uptime','?')}`"
                        f"· commands `{ctx.get('cmd','?')}`"
                    ),
                    footer="tap ▸ back",
                    width=46,
                )
            ],
            "keyboard": None,
        }

    register("stats", "stats", "System Stats", render_stats)

    # ---- Settings app ----
    def render_settings(context: Dict[str, Any]) -> Dict[str, Any]:
        from renderer import build_panel

        return {
            "blocks": [
                build_panel(
                    title="Settings",
                    content="themes, shortcuts, preferences",
                    footer="tap ▸ back",
                    width=46,
                )
            ],
            "keyboard": None,
        }

    register("settings", "settings", "Settings", render_settings)

    # ---- Help app ----
    def render_help(context: Dict[str, Any]) -> Dict[str, Any]:
        from renderer import build_panel

        return {
            "blocks": [
                build_panel(
                    title="Help & Commands",
                    content=(
                        "/start · /help · /theme [name] · /stats · /clear · /status · /app <name>"
                    ),
                    footer="tap ▸ back",
                    width=46,
                )
            ],
            "keyboard": None,
        }

    register("help", "help", "Help & Commands", render_help)


# Load built-in apps on import
load_builtin_apps()
