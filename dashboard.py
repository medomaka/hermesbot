"""
dashboard.py — Dashboard renderer + inline navigation.

Produces the home "terminal dashboard" panel: a themed card-grid of
functional sections. Each card is an inline keyboard button that opens
into a sub-panel (app route). The dashboard also carries live system
metrics and a theme switcher.

The dashboard is the default landing page and the navigation hub.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from theme import get_theme, Theme
from renderer import (
    render_blocks,
    build_panel,
    build_code,
    build_prompt,
    escape_md,
)

# ---- Section definitions ----
# Each section maps a route name -> (icon, title, description, callback action)

SECTION_ICONS = {
    "chat":        "✦",
    "media":       "◈",
    "files":       "▤",
    "calls":       "◉",
    "stats":       "▣",
    "settings":    "⚙",
    "help":        "❯",
    "apps":        "▣",
}

SECTION_ROUTES = [
    ("chat",    "Assistant Chat",   "Live chat with the assistant, commands & AI"),
    ("media",   "Media Studio",     "Images, video & rich media tools"),
    ("files",   "File Manager",     "Browse, upload & manage files"),
    ("calls",   "Live Calls",       "Voice-call into the bot (live)"),
    ("stats",   "System Stats",     "Session, command & uptime metrics"),
    ("settings","Settings",        "Themes, shortcuts & preferences"),
    ("help",    "Help & Commands", "Command reference & guides"),
    ("apps",    "Installed Apps",   "Load app modules & plugins"),
]

# Status metrics shown on the dashboard
def default_vars() -> Dict[str, str]:
    return {
        "session": "001",
        "uptime": "2h 14m",
        "cmd": "0",
        "theme": get_theme().name,
    }


@dataclass
class Dashboard:
    title: str = "TERMINAL DASHBOARD"
    subtitle: str = "v1.0.0 — terminal-style interface"
    assets: Callable[[], Dict[str, str]] = default_vars

    def build(self) -> Dict[str, Any]:
        """Build the dashboard message blocks + inline keyboard."""
        vars_ = self.assets()
        blocks: List[Dict[str, Any]] = []
        blocks.append(build_panel(
            title=self.title,
            content=self.subtitle,
            footer="use /help or tap a section to open",
            width=46,
        ))

        # Build each section card
        rows: List[List[Dict[str, Any]]] = []
        for route, title, desc in SECTION_ROUTES:
            rows.append([self._section_card(route, title, desc, vars_)])

        # Add the apps browser and commands rows
        rows.append([self._apps_card()])
        rows.append([self._commands_card()])

        # Assemble panel content with sections
        content = "\n\n".join(
            f"`{i+1}. `{title} — {desc}" for i, (route, title, desc) in enumerate(SECTION_ROUTES)
        )
        # Append apps & commands
        content += "\n\n`9. `Apps Library"
        content += "\n`10. `Command Palette"

        # Verbose terminal-style layout: each section becomes a "panel" style block
        # We'll render as a series of bordered mini-panels
        content_parts: List[str] = []

        # Stats footer
        stats_footer = (
            f"session `{vars_['session']}` · uptime `{vars_['uptime']}` "
            f"· commands `{vars_['cmd']}` · theme `{vars_['theme']}`"
        )

        content_parts.append(f"{build_panel('Sections', content, footer=stats_footer, width=46)}")

        # Build the message
        message_blocks = []
        # Header
        message_blocks.append({
            "type": "header",
            "title": self.title,
            "subtitle": self.subtitle,
        })
        # Quick command hint
        message_blocks.append({
            "type": "text",
            "content": "tap a ▸ section to open · /help for commands · /theme [name] to switch",
        })
        # Each section as a panel
        for route, title, desc in SECTION_ROUTES:
            message_blocks.append(self._section_panel(route, title, desc))
        message_blocks.append(self._apps_panel())
        message_blocks.append(self._commands_panel())

        keyboard = self._build_keyboard()

        return {"blocks": message_blocks, "keyboard": keyboard}

    # ---- Section sub-panels ----
    def _section_panel(self, route: str, title: str, desc: str) -> Dict[str, Any]:
        return {
            "type": "panel",
            "title": f"{SECTION_ICONS.get(route, '▸')} {title}",
            "content": desc,
            "footer": "tap ▸ back to return to dashboard",
            "width": 46,
        }

    def _apps_panel(self) -> Dict[str, Any]:
        return {
            "type": "panel",
            "title": "Apps Library",
            "content": "load `app <name>` to run a module · /install <name>",
            "footer": "tap ▸ back",
            "width": 46,
        }

    def _commands_panel(self) -> Dict[str, Any]:
        cmds = ["/start", "/help", "/theme", "/stats", "/clear", "/status"]
        return {
            "type": "code",
            "lang": "commands",
            "content": "\n".join(f"`{c}`" for c in cmds),
        }

    def _section_card(self, route: str, title: str, desc: str, vars_: Dict[str, str]) -> Dict[str, Any]:
        return {
            "type": "card",
            "icon": SECTION_ICONS.get(route, "▸"),
            "title": title,
            "desc": desc,
        }

    def _apps_card(self) -> Dict[str, Any]:
        return {
            "type": "card",
            "icon": "▣",
            "title": "Apps Library",
            "desc": "load `app <name>` to run a module",
        }

    def _commands_card(self) -> Dict[str, Any]:
        return {
            "type": "card",
            "icon": "❯",
            "title": "Command Palette",
            "desc": "/help, /theme, /status, /stats, /clear",
        }

    # ---- Inline keyboard routing ----
    def _build_keyboard(self) -> Optional[Dict[str, Any]]:
        """Return an inline keyboard mapping sections -> callback routes.

        The dispatcher intercepts 'dashboard:<route>' callbacks and renders
        the matching panel. 'theme' and 'back' are handled as special keys.
        """
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton

        rows: List[List[Dict[str, Any]]] = []
        for route, title, desc in SECTION_ROUTES:
            rows.append([{"action": "button", "text": f"▸ {title}", "callback": f"route:{route}"}])

        rows.append([{"action": "button", "text": "Theme", "callback": "theme"}])
        rows.append([{"action": "button", "text": "Back", "callback": "dashboard"}])

        kb = InlineKeyboardMarkup(rows)
        return {"action": "keyboard", "value": kb}


# ---- Convenient builder ----
dash = Dashboard()
