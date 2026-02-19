# -*- coding: utf8 -*-
#
#  platform_ble/__init__.py
#  Platform BLE backend factory for CyKIT.
#


def get_ble_backend():
    """Return a BLE backend instance appropriate for the current platform."""
    from .bleak_backend import BleakBLEBackend
    return BleakBLEBackend()
