class TelegramError(Exception):
    def __init__(
        self,
        message: str,
        *,
        uncertain: bool = False,
        missing: bool = False,
        not_modified: bool = False,
    ) -> None:
        self.message = message
        self.uncertain = uncertain
        self.missing = missing
        self.not_modified = not_modified
        super().__init__(message)
