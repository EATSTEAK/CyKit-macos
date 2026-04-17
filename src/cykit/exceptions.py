class CyKitError(Exception):
    """Base exception for public CyKit API failures."""


class DiscoveryError(CyKitError):
    """Raised when device discovery fails."""


class ConnectionError(CyKitError):
    """Raised when a device connection cannot be established or maintained."""


class StreamError(CyKitError):
    """Raised when streaming cannot continue."""


class ControlError(CyKitError):
    """Raised when a runtime control operation fails."""


class RecordingError(CyKitError):
    """Raised when recording cannot be started or stopped."""
