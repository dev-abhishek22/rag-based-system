from src.cli.theme import DEFAULT_THEME


class CliSession:
    def __init__(self):
        self.top_k = 5
        self.raw_mode = False
        self.show_sources = True
        self.history = []
        self.theme_name = DEFAULT_THEME
