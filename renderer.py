"""
renderer.py — Rich message renderer for the terminal-style Telegram bot.

Transforms structured message "blocks" into Telegram-rendered rich content
with a consistent terminal aesthetic: monospace prompts, bordered panels,
code blocks, status indicators, and themed headers.

The renderer is framework-agnostic. It returns:
  - body: a MarkdownV2-escaped, terminal-styled string
  - keyboard: an InlineKeyboardMarkup (or None)
  - media: a list of media (for future rich attachments)

Theme colors are applied via monospace backticks, borders, symbols, and a
per-theme legend so the UI reads as a "terminal app" inside Telegram.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from theme import get_theme, Theme

# ---- MarkdownV2 escaping (escape all special chars) ----
_MARKDOWN_ESCAPE_RE = re.compile(r'([\\*_`\\[~])')


def escape_md(text: str) -> str:
    """Escape Telegram MarkdownV2 special characters."""
    return _MARKDOWN_ESCAPE_RE.sub(r'\\', text)


# ---- Block type registry ----
# Message blocks are dicts with a "type" key.
# The renderer converts each block into styled segments.


def _render_text(block: Dict[str, Any], theme: Theme) -> str:
    content = block.get("content", "")
    # Prompt-like prefix: show command/echo
    if block.get("prefix"):
        prefix = block["prefix"]
        return f"<{prefix}> {escape_md(content)}"
    return escape_md(content)


def _render_code(block: Dict[str, Any], theme: Theme) -> str:
    content = block.get("content", "")
    lang = block.get("lang", "")
    header = f"#{lang}" if lang else "CODE"
    lines = content.splitlines()
    # Use backticks for monospace code blocks; fold long lines
    body = "\n".join(lines) if lines else "(empty)"
    return f"`{header}`\n`{body}`"


def _render_panel(block: Dict[str, Any], theme: Theme) -> str:
    """Bordered panel with title, content, and optional footer/actions."""
    title = block.get("title", "")
    content = block.get("content", "")
    footer = block.get("footer", "")
    width = block.get("width", 46)

    # Simple box drawing
    top = block.get("top", "┌" + "─" * (width - 2) + "┐")
    bottom = block.get("bottom", "└" + "─" * (width - 2) + "┘")
    side = "│"

    lines = []
    if title:
        lines.append(f"{side} {escape_md(title)}".ljust(width - 1) + " " + side)
    if content:
        # Wrap long content
        import textwrap
        wrapped = textwrap.wrap(escape_md(content), width - 4) or ["(empty)"]
        for ln in wrapped:
            lines.append(f"{side} {ln}".ljust(width - 1) + " " + side)
    if footer:
        lines.append(f"{side} {footer}".ljust(width - 1) + " " + side)
    # Join with side
    body_lines = [side + ln + " " + side for ln in lines]
    return "\n".join([top] + body_lines + [bottom])


def _render_prompt(block: Dict[str, Any], theme: Theme) -> str:
    """Command prompt: user ▸ command"""
    user = block.get("user", "user")
    command = block.get("command", "")
    return f"<{user}> ▸ {escape_md(command)}"


def _render_divider(block: Dict[str, Any], theme: Theme) -> str:
    ch = block.get("char", "─")
    width = block.get("width", 46)
    return ch * width


def _render_header(block: Dict[str, Any], theme: Theme) -> str:
    title = block.get("title", "")
    sub = block.get("subtitle", "")
    tag = block.get("tag", theme.name.upper())
    line = f"═" * 46
    parts = [f"▸ {escape_md(title)}", f"▸ {escape_md(sub)}" if sub else ""]
    return "\n".join(parts)


def _render_card(block: Dict[str, Any], theme: Theme) -> str:
    """Compact card: title + description + optional actions hint."""
    title = block.get("title", "")
    desc = block.get("desc", "")
    icon = block.get("icon", "▸")
    parts = [f"{icon} {escape_md(title)}"]
    if desc:
        parts.append(escape_md(desc))
    return "  ".join(parts)


def _render_status(block: Dict[str, Any], theme: Theme) -> str:
    status = block.get("status", "ok")
    label = block.get("label", status)
    icons = {"ok": "✔", "error": "✖", "warning": "⚠", "processing": "⟳"}
    icon = icons.get(status, "●")
    color = {"ok": theme.palette.success, "error": theme.palette.error,
             "warning": theme.palette.warning, "processing": theme.palette.primary}
    return f"`[{icon}]` {escape_md(label)}  `{color.get(status, 'dim')}`"


def _render_legend(block: Dict[str, Any], theme: Theme) -> str:
    """Show the active theme palette + palette meaning."""
    p = theme.palette
    return (
        f"Theme: `{theme.name}` ▐ primary [`{p.primary}`] "
        f"▐ accent [`{p.accent}`] ▐ ✓ success [`{p.success}`] "
        f"▐ ⚠ warning [`{p.warning}`] ▐ ✖ error [`{p.error}`]"
    )


# ---- Block renderers keyed by type ----
_DEFAULT_RENDERERS = {
    "text": _render_text,
    "code": _render_code,
    "panel": _render_panel,
    "prompt": _render_prompt,
    "divider": _render_divider,
    "header": _render_header,
    "card": _render_card,
    "status": _render_status,
    "legend": _render_legend,
}


def render_block(block: Dict[str, Any], theme: Theme | None = None) -> str:
    """Render a single message block to styled text."""
    t = theme or get_theme()
    rtype = block.get("type", "text")
    renderer = _DEFAULT_RENDERERS.get(rtype)
    if renderer is None:
        return escape_md(str(block))
    return renderer(block, t)


def render_blocks(
    blocks: List[Dict[str, Any]],
    theme: Theme | None = None,
    include_legend: bool = True,
) -> Tuple[str, Dict[str, Any]]:
    """
    Render a full message from a list of blocks.

    Returns (body, extras) where extras holds keyboard/media for the dispatcher.
    """
    theme = theme or get_theme()
    body_lines: List[str] = []
    for blk in blocks:
        if blk.get("type") == "legend" and not include_legend:
            continue
        body_lines.append(render_block(blk, theme))

    body = "\n\n".join(body_lines).strip()
    extras: Dict[str, Any] = {"keyboard": None, "media": []}
    return body, extras


# ---- Convenient factory ----
def build_panel(
    title: str,
    content: str,
    footer: str = "",
    width: int = 46,
    **kw,
) -> Dict[str, Any]:
    """Build a panel block."""
    return {
        "type": "panel",
        "title": title,
        "content": content,
        "footer": footer,
        "width": width,
        **kw,
    }


def build_code(lang: str, content: str) -> Dict[str, Any]:
    return {"type": "code", "lang": lang, "content": content}


def build_prompt(user: str, command: str) -> Dict[str, Any]:
    return {"type": "prompt", "user": user, "command": command}
