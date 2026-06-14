from dataclasses import dataclass


@dataclass
class CliFeature:
    command: str
    shortcut: str
    title: str
    description: str


CLI_FEATURES = [
    CliFeature("/help", "?", "Help", "Show commands and examples"),
    CliFeature("/topk", "k", "Top-K", "Change number of search results"),
    CliFeature("/theme", "t", "Theme", "Switch CLI theme"),
    CliFeature("/raw", "r", "Raw", "Toggle raw payload output"),
    CliFeature("/sources", "s", "Sources", "Toggle source table"),
    CliFeature("/history", "h", "History", "View previous searches"),
    CliFeature("/clear", "c", "Clear", "Clear the terminal"),
    CliFeature("/exit", "q", "Exit", "Quit RevSearch"),
]

COMMAND_WORDS = [feature.command for feature in CLI_FEATURES]
