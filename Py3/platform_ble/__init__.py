# -*- coding: utf8 -*-
#
#  platform_ble/__init__.py
#  Platform BLE backend factory for CyKIT.
#

import platform as _platform


def get_ble_backend():
    """Return a BLE backend instance appropriate for the current platform.

    On macOS/Linux, returns a bleak-based backend.
    On Windows, returns None (caller should fall back to the EEGBtleLib DLL).
    """
    system = _platform.system()
    if system in ('Darwin', 'Linux'):
        from .bleak_backend import BleakBLEBackend
        return BleakBLEBackend()
    return None
