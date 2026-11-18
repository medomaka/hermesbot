"""smoke test: import all modules, render a dashboard, print result."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from theme import get_theme, list_themes, THEMES
from renderer import render_blocks, build_panel, build_code
from dashboard import Dashboard, SECTION_ROUTES
from apps import list_apps
from router import Router

def main():
    print("themes:", list_themes())
    print("theme palette keys:", sorted(THEMES["solar"].palette.__dict__.keys()))
    theme = get_theme("terminal")
    print("active theme:", theme.name, "primary:", theme.palette.primary)

    # Render a panel block
    panel = build_panel("Test", "Hello world", footer="tap ▸ back", width=20)
    out = render_blocks([panel], theme=theme)
    print("\n-- panel --")
    print(out[0])

    # Render a code block
    code = build_code("py", "print('hi')")
    out = render_blocks([code], theme=theme)
    print("\n-- code --")
    print(out[0])

    # Dashboard
    dash = Dashboard()
    result = dash.build()
    print("\n-- dashboard --")
    print("blocks:", len(result["blocks"]))
    print("keyboard action:", result["keyboard"]["action"])
    print("first panel title:", result["blocks"][0]["title"])

    # Apps registry
    print("\napps:", list_apps())

    # Router
    r = Router()
    print("\ncommands:", list(r.commands))
    print("callbacks:", list(r.callbacks))

    # Inline keyboard text (sanity check the route text)
    print("\nOK — all modules import and render.")

if __name__ == "__main__":
    main()
