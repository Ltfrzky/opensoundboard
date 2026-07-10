class OpenSoundboardError(Exception):
    """Base class for expected, user-facing application errors."""


class InvalidSoundError(OpenSoundboardError):
    """Raised when supplied sound data is invalid."""


class BoardNotEmptyError(OpenSoundboardError):
    """Raised when a board containing sounds is deleted."""
