class OpenSoundboardError(Exception):
    """Base class for expected, user-facing application errors."""


class InvalidSoundError(OpenSoundboardError):
    """Raised when supplied sound data is invalid."""


class BoardNotEmptyError(OpenSoundboardError):
    """Raised when a board containing sounds is deleted."""


class InvalidHotkeyError(OpenSoundboardError):
    """Raised when a hotkey cannot be parsed or is reserved."""


class HotkeyConflictError(OpenSoundboardError):
    """Raised when a hotkey is already assigned to another action."""


class HotkeyRegistrationError(OpenSoundboardError):
    """Raised when a valid hotkey cannot be registered by the backend."""
