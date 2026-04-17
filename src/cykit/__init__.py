"""CyKIT public library API for Emotiv EEG headset acquisition."""

from .client import CyKitClient
from .discovery import discover
from .exceptions import ConnectionError, ControlError, CyKitError, DiscoveryError, RecordingError, StreamError
from .models import ConnectionOptions, DataMode, DeviceInfo, Model, OutputOptions, Sample, StreamOptions, Transport

__version__ = "4.0.0"

__all__ = [
    "CyKitClient",
    "ConnectionError",
    "ConnectionOptions",
    "ControlError",
    "CyKitError",
    "DataMode",
    "DeviceInfo",
    "DiscoveryError",
    "Model",
    "OutputOptions",
    "RecordingError",
    "Sample",
    "StreamError",
    "StreamOptions",
    "Transport",
    "discover",
]
