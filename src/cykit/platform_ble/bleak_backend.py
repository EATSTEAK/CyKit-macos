# -*- coding: utf8 -*-
#
#  platform_ble/bleak_backend.py
#  macOS / Linux BLE backend using the bleak library (CoreBluetooth / BlueZ).
#

import asyncio
import threading
import queue

from .base import BLEBackend

try:
    import bleak
except ImportError:
    raise ImportError(
        "The 'bleak' package is required for Bluetooth on macOS/Linux. "
        "Install it with: pip install bleak   (or: uv add bleak)"
    )


class BleakBLEBackend(BLEBackend):
    """BLE backend that wraps *bleak* (async) into CyKIT's sync/threading model."""

    # Emotiv GATT UUIDs
    DEVICE_UUID = "81072f40-9f3d-11e3-a9dc-0002a5d5c51b"
    DATA_UUID   = "81072f41-9f3d-11e3-a9dc-0002a5d5c51b"
    MEMS_UUID   = "81072f42-9f3d-11e3-a9dc-0002a5d5c51b"

    def __init__(self):
        self._device = None       # bleak.BLEDevice from scan
        self._client = None       # bleak.BleakClient
        self._loop = None         # dedicated asyncio event loop
        self._loop_thread = None  # daemon thread running the loop
        self._connected = False
        self._device_name = ""
        self._hex_key = ""
        self._start_event_loop()

    # ------------------------------------------------------------------
    #  Asyncio event loop management
    # ------------------------------------------------------------------

    def _start_event_loop(self):
        """Spin up a dedicated asyncio event loop in a daemon thread."""
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._loop.run_forever,
            name="bleakEventLoop",
            daemon=True,
        )
        self._loop_thread.start()

    def _run_coroutine(self, coro, timeout=30.0):
        """Schedule *coro* on the background loop and block until it completes."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    # ------------------------------------------------------------------
    #  BLEBackend interface
    # ------------------------------------------------------------------

    def discover_devices(self, timeout=10.0):
        return self._run_coroutine(self._async_discover(timeout), timeout=timeout + 5)

    def scan_for_device(self, name_filter, manual_key="AUTO-DETECT", timeout=10.0):
        return self._run_coroutine(
            self._async_scan(name_filter, manual_key, timeout),
            timeout=timeout + 5,
        )

    async def _async_discover(self, timeout):
        scanner = bleak.BleakScanner()
        devices = await scanner.discover(timeout=timeout)
        results = []
        for device in devices:
            if not device.name:
                continue
            raw_name = device.name.replace("(", " ").replace(")", " ").strip()
            parts = raw_name.split()
            device_type = parts[0] if parts else raw_name
            device_key = parts[1] if len(parts) > 1 and len(parts[1]) == 8 else None
            if device_type not in {"Insight", "EPOC", "EPOC+"}:
                continue
            results.append(
                {
                    "name": device.name,
                    "device_type": device_type,
                    "device_key": device_key,
                    "address": getattr(device, "address", None),
                    "rssi": getattr(device, "rssi", None),
                }
            )
        return results

    async def _async_scan(self, name_filter, manual_key, timeout):
        devices = await self._async_discover(timeout)

        for device in devices:
            device_name = device["name"]
            dev_type = device["device_type"]
            hex_key = device["device_key"]
            if name_filter not in device_name or hex_key is None:
                continue
            if manual_key != "AUTO-DETECT" and hex_key != manual_key:
                continue
            scanner = bleak.BleakScanner()
            discovered = await scanner.discover(timeout=0.1)
            for candidate in discovered:
                if candidate.name == device_name:
                    self._device = candidate
                    break
            self._device_name = dev_type
            self._hex_key = hex_key
            return (dev_type, hex_key)

        raise RuntimeError(
            f"No BLE device with '{name_filter}' in name found (timeout={timeout}s)"
        )

    def connect(self, timeout=10.0):
        if self._device is None:
            raise RuntimeError("No device scanned yet. Call scan_for_device() first.")
        self._run_coroutine(self._async_connect(), timeout=timeout + 5)

    async def _async_connect(self):
        self._client = bleak.BleakClient(
            self._device,
            disconnected_callback=self._on_disconnect,
        )
        await self._client.connect()
        self._connected = True

    def subscribe_notifications(self, char_uuid, callback):
        """Subscribe to notifications. *callback(bytearray)* is called from the
        bleak event-loop thread — it must be thread-safe (e.g. queue.put)."""
        self._run_coroutine(
            self._async_subscribe(char_uuid, callback),
            timeout=10,
        )

    async def _async_subscribe(self, char_uuid, callback):
        def _handler(_sender, data: bytearray):
            callback(bytearray(data))

        await self._client.start_notify(char_uuid, _handler)

    def disconnect(self):
        if self._client and self._connected:
            try:
                self._run_coroutine(self._client.disconnect(), timeout=5)
            except Exception:
                pass
        self._connected = False

    def is_connected(self):
        return self._connected

    # ------------------------------------------------------------------
    #  Properties
    # ------------------------------------------------------------------

    @property
    def device_name(self):
        return self._device_name

    @property
    def hex_key(self):
        return self._hex_key

    # ------------------------------------------------------------------
    #  Internal
    # ------------------------------------------------------------------

    def _on_disconnect(self, _client):
        self._connected = False
