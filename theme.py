"""
theme.py — Theming system for the terminal-style Telegram bot.

Provides a Theme registry: each theme has a color palette + render helpers
that wrap Telegram MarkdownV2 into a consistent "terminal" aesthetic.
Themes are swappable at runtime, and the renderer applies the active theme.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

# Telegram MarkdownV2 special characters that must be escaped
MD_ESCAPE = r"\`*_[~"


@dataclass
class ThemePalette:
    """Color palette for a theme. Values map to Telegram MarkdownV2 semantics."""
    bg: str
    fg: str
    primary: str
    secondary: str
    accent: str
    code: str
    success: str
    warning: str
    error: str
    dim: str
    border: str


@dataclass
class Theme:
    name: str
    palette: ThemePalette
    font: str = "mono"
    style: str = "terminal"

    def __post_init__(self):
        if isinstance(self.palette, dict):
            self.palette = ThemePalette(**self.palette)


# ---- Palette definitions ----

TERMINAL_PALETTE = ThemePalette(
    bg="#0a0a0a", fg="#e6e6e6", primary="#00ff41", secondary="#ff6400",
    accent="#7c4dff", code="#111", success="#00ff41", warning="#ff6400",
    error="#ff3355", dim="#6e6e6e", border="#2a2a2a",
)

MIDNIGHT_PALETTE = ThemePalette(
    bg="#0d1117", fg="#c9d1d9", primary="#2ea043", secondary="#f0883e",
    accent="#9a7fff", code="#080c12", success="#2ea043", warning="#f0883e",
    error="#ff5630", dim="#6e6e6e", border="#1e242e",
)

OCEAN_PALETTE = ThemePalette(
    bg="#0b1422", fg="#d4e4f7", primary="#00a6ff", secondary="#ff9e3e",
    accent="#9a70ff", code="#040a12", success="#00a6ff", warning="#ff9e3e",
    error="#ff3366", dim="#6b8ba8", border="#15263c",
)

SOLAR_PALETTE = ThemePalette(
    bg="#05060a", fg="#e8eaf0", primary="#3b82f6", secondary="#f59e0b",
    accent="#a855f7", code="#0a0c14", success="#22c55e", warning="#f59e0b",
    error="#ef4444", dim="#8a93a6", border="#1a1f2e",
)


# ---- Theme registry ----

THEMES: Dict[str, Theme] = {
    "terminal": Theme("terminal", TERMINAL_PALETTE),
    "midnight": Theme("midnight", MIDNIGHT_PALETTE),
    "ocean": Theme("ocean", OCEAN_PALETTE),
    "solar": Theme("solar", SOLAR_PALETTE),
}

# The active theme
_active = THEMES["solar"]


def get_theme(name: str | None = None) -> Theme:
    """Return the named theme, defaulting to the active one."""
    global _active
    if name is None:
        return _active
    if name not in THEMES:
        raise KeyError(f"Unknown theme: {name!r}. Available: {list(THEMES)}")
    _active = THEMES[name]
    return _active


def list_themes() -> list[str]:
    return list(THEMES.keys())


def set_theme(name: str) -> None:
    get_theme(name)  # validates & sets active
