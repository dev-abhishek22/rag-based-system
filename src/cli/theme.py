from prompt_toolkit.styles import Style

THEMES = {
    "hacker": {
        "primary": "bright_green",
        "secondary": "green",
        "accent": "spring_green2",
        "muted": "grey70",
        "success": "bright_green",
        "warning": "yellow",
        "error": "red",
        "info": "bright_cyan",
        "prompt_primary": "\033[92m",
        "prompt_accent": "\033[38;5;120m",
        "completion_fg": "#7CFFB2",
        "completion_meta_fg": "#8A8F98",
        "completion_selected_fg": "#7CFFB2",
    },
    "ocean": {
        "primary": "bright_cyan",
        "secondary": "cyan",
        "accent": "deep_sky_blue1",
        "muted": "grey70",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "info": "bright_cyan",
        "prompt_primary": "\033[96m",
        "prompt_accent": "\033[38;5;39m",
        "completion_fg": "#67E8F9",
        "completion_meta_fg": "#8A8F98",
        "completion_selected_fg": "#67E8F9",
    },
    "sunset": {
        "primary": "bright_magenta",
        "secondary": "magenta",
        "accent": "hot_pink",
        "muted": "grey70",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "info": "bright_magenta",
        "prompt_primary": "\033[95m",
        "prompt_accent": "\033[38;5;205m",
        "completion_fg": "#FF8BD1",
        "completion_meta_fg": "#8A8F98",
        "completion_selected_fg": "#FF8BD1",
    },
    "amber": {
        "primary": "yellow",
        "secondary": "gold1",
        "accent": "orange3",
        "muted": "grey70",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "info": "yellow",
        "prompt_primary": "\033[93m",
        "prompt_accent": "\033[38;5;214m",
        "completion_fg": "#FFD166",
        "completion_meta_fg": "#8A8F98",
        "completion_selected_fg": "#FFD166",
    },
}


DEFAULT_THEME = "hacker"


def get_theme(name: str = DEFAULT_THEME):
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def get_prompt_style(theme_name: str = DEFAULT_THEME):
    theme = get_theme(theme_name)

    return Style.from_dict(
        {
            "toolbar": f"bg:default {theme['completion_meta_fg']}",
            "completion-menu": "bg:default",
            "completion-menu.completion": f"bg:default {theme['completion_fg']}",
            "completion-menu.completion.current": (
                f"bg:default {theme['completion_selected_fg']} bold"
            ),
            "completion-menu.meta": f"bg:default {theme['completion_meta_fg']}",
            "completion-menu.meta.completion": (
                f"bg:default {theme['completion_meta_fg']}"
            ),
            "completion-menu.meta.completion.current": (
                f"bg:default {theme['completion_meta_fg']}"
            ),
            "scrollbar.background": "bg:default",
            "scrollbar.button": "bg:default",
        }
    )
