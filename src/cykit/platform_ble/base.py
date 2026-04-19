# -*- coding: utf8 -*-
#
#  platform_ble/base.py
#  Abstract BLE interface for CyKIT cross-platform Bluetooth LE support.
#

import abc


class BLEBackend(abc.ABC):
    """Abstract base class for platform-specific BLE backends."""

    @abc.abstractmethod
    def discover_devices(self, timeout=10.0, probe_gatt=True, probe_timeout=2.0):
        """Return nearby CyKit-compatible BLE devices as dictionaries."""
        ...

    @abc.abstractmethod
    def scan_for_device(self, name_filter, manual_key="AUTO-DETECT", timeout=10.0):
        """Scan for a BLE device whose name contains *name_filter*.

        Args:
            name_filter: Substring to match in advertised device names
                         (e.g. "Insight", "EPOC").
            manual_key:  8-hex-digit key from the device name, or
                         "AUTO-DETECT" to accept any matching device.
            timeout:     Scan duration in seconds.

        Returns:
            A tuple (device_name, hex_key) on success, or raises RuntimeError.
        """
        ...

    @abc.abstractmethod
    def connect(self, timeout=10.0):
        """Connect to the device found by the last scan.

        Args:
            timeout: Connection timeout in seconds.
        """
        ...

    @abc.abstractmethod
    def subscribe_notifications(self, char_uuid, callback):
        """Subscribe to GATT characteristic notifications.

        Args:
            char_uuid: UUID string of the characteristic.
            callback:  Callable receiving ``bytearray`` data on each notification.
        """
        ...

    @abc.abstractmethod
    def disconnect(self):
        """Disconnect from the device and release resources."""
        ...

    @abc.abstractmethod
    def is_connected(self):
        """Return True if a device is currently connected."""
        ...
