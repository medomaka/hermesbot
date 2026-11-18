"""
router.py — Command router + inline keyboard callback router.

Maps incoming Telegram updates to handler functions:
  - Text messages that start with '/' -> command handler
  - Inline keyboard callbacks -> callback handler
  - Everything else -> message handler (with auto-reply + dashboard option)

The router is a lightweight, framework-agnostic dispatch layer. It expects
callbacks to be registered via @router.command(...) and @router.callback(...).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Optional

# Type aliases
Handler = Callable[..., Awaitable[Any]]
CommandHandler = Callable[[], Awaitable[Any]]
CallbackHandler = Callable[[Dict[str, Any]], Awaitable[Any]]


class Router:
    """Dispatch router for the terminal bot."""

    def __init__(self):
        self.commands: Dict[str, Handler] = {}
        self.callbacks: Dict[str, Handler] = {}
        self.default_message: Handler | None = None
        self.default_callback: Handler | None = None

    # ---- registration ----
    def command(self, name: str, help_text: str = ""):
        """Decorator: register a slash command handler."""
        def deco(fn: Handler) -> Handler:
            self.commands[name.lstrip("/").lower()] = fn
            fn.__help__ = help_text or name
            return fn
        return deco

    def callback(self, pattern: str):
        """Decorator: register a callback handler by route pattern."""
        def deco(fn: Handler) -> Handler:
            self.callbacks[pattern] = fn
            return fn
        return deco

    def message(self, fn: Handler):
        """Register the default message handler (any non-command text)."""
        self.default_message = fn
        return fn

    def callback_handler(self, fn: Handler):
        self.default_callback = fn
        return fn

    # ---- dispatch ----
    def route_command(self, raw: str) -> Optional[str]:
        """Normalize a raw text message into a command name."""
        s = raw.strip()
        if not s:
            return None
        if s.startswith("/"):
            return s.split()[0].lower()
        return None

    async def handle_text(self, text: str, context: Dict[str, Any]) -> Any:
        """Route a text message."""
        cmd = self.route_command(text)
        if cmd:
            handler = self.commands.get(cmd)
            if handler:
                return await handler(context)
            # unknown command
            return await self._unknown_command(cmd)
        if self.default_message:
            return await self.default_message(context)
        return await self._default_reply(context)

    async def handle_callback(self, data: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Route an inline keyboard callback query."""
        payload = data.get("payload", "")
        # Match most-specific pattern first
        for pattern, handler in self.callbacks.items():
            if self._pattern_matches(pattern, payload):
                return await handler({**data, **context})
        if self.default_callback:
            return await self.default_callback({**data, **context})
        # show dashboard for unknown callbacks
        return await self._dashboard_fallback(context)

    def _pattern_matches(self, pattern: str, payload: str) -> bool:
        if pattern.startswith("route:"):
            return payload == pattern.split(":", 1)[1]
        # simple substring match
        return pattern in payload

    # ---- built-in handlers ----
    async def _unknown_command(self, cmd: str) -> str:
        return (
            f"`✖` unknown command `{cmd}`\n"
            f"/help for the command palette"
        )

    async def _default_reply(self, context: Dict[str, Any]) -> str:
        return (
            "Type a command or tap a ▸ section on the dashboard.\n"
            "/help to open the command palette."
        )

    async def _dashboard_fallback(self, context: Dict[str, Any]) -> str:
        return (
            "No action for that button. Return to the dashboard with /dashboard."
        )


# ---- global singleton ----
router = Router()
