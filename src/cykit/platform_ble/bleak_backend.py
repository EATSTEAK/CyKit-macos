# -*- coding: utf8 -*-
#
#  platform_ble/bleak_backend.py
#  macOS / Linux BLE backend using the bleak library (CoreBluetooth / BlueZ).
#

import asyncio
import threading
import queue
import json

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

    def discover_devices(self, timeout=10.0, probe_gatt=True, probe_timeout=2.0):
        total_timeout = timeout + (probe_timeout * 4 if probe_gatt else 5)
        return self._run_coroutine(self._async_discover(timeout, probe_gatt=probe_gatt, probe_timeout=probe_timeout), timeout=total_timeout)

    def scan_for_device(self, name_filter, manual_key="AUTO-DETECT", timeout=10.0):
        normalized_key = manual_key.upper() if isinstance(manual_key, str) else manual_key
        return self._run_coroutine(
            self._async_scan(name_filter, normalized_key, timeout),
            timeout=timeout + 5,
        )

    def _is_emotiv_candidate(self, raw_name, device_type, device_key):
        normalized = (raw_name or "").lower()
        return (
            device_type in {"Insight", "Insight2", "EPOC", "EPOC+"}
            or "insight" in normalized
            or "epoc" in normalized
            or device_key is not None
        )

    async def _probe_device_gatt(self, device, probe_timeout):
        services_seen = []
        try:
            client = bleak.BleakClient(device)
            await asyncio.wait_for(client.connect(), timeout=probe_timeout)
            try:
                services = await client.get_services()
            except AttributeError:
                services = client.services
            if services is None:
                services = []
            matched = False
            for service in services:
                uuid = str(getattr(service, "uuid", "")).lower()
                services_seen.append(uuid)
                if uuid in {self.DEVICE_UUID, self.DATA_UUID, self.MEMS_UUID}:
                    matched = True
                for characteristic in getattr(service, "characteristics", []):
                    char_uuid = str(getattr(characteristic, "uuid", "")).lower()
                    services_seen.append(char_uuid)
                    if char_uuid in {self.DEVICE_UUID, self.DATA_UUID, self.MEMS_UUID}:
                        matched = True
            return {
                "gatt_match": matched,
                "gatt_services": sorted(set(services_seen)),
                "probe_error": None,
            }
        except Exception as exc:
            return {
                "gatt_match": False,
                "gatt_services": sorted(set(services_seen)),
                "probe_error": str(exc),
            }
        finally:
            try:
                if 'client' in locals() and client.is_connected:
                    await client.disconnect()
            except Exception:
                pass

    def _device_metadata(self, device):
        raw_device_name = getattr(device, "name", None)
        normalized_name = (raw_device_name or "").replace("(", " ").replace(")", " ").strip()
        parts = normalized_name.split() if normalized_name else []
        device_type = parts[0] if parts else None
        device_key = None
        for part in parts[1:]:
            if len(part) == 8 and all(char in "0123456789abcdefABCDEF" for char in part):
                device_key = part.upper()
                break
        return {
            "name": raw_device_name,
            "raw_name": raw_device_name,
            "device_type": device_type,
            "device_key": device_key,
            "address": getattr(device, "address", None),
            "rssi": getattr(device, "rssi", None),
            "matched_known_type": device_type in {"Insight", "Insight2", "EPOC", "EPOC+"},
            "has_name": bool(raw_device_name),
            "has_device_key": device_key is not None,
            "service_uuids": [],
            "gatt_match": False,
            "gatt_services": [],
            "probe_error": None,
        }

    async def _async_discover(self, timeout, probe_gatt=True, probe_timeout=2.0):
        scanner = bleak.BleakScanner()
        devices = await scanner.discover(timeout=timeout)
        results = []
        for device in devices:
            metadata = self._device_metadata(device)
            if probe_gatt and self._is_emotiv_candidate(metadata["name"], metadata["device_type"], metadata["device_key"]):
                metadata.update(await self._probe_device_gatt(device, probe_timeout))
            results.append(metadata)
        return results

    async def _async_scan(self, name_filter, manual_key, timeout):
        discovered = await bleak.BleakScanner().discover(timeout=timeout)
        devices = [self._device_metadata(device) | {"_device": device} for device in discovered]

        ranked_devices = sorted(
            devices,
            key=lambda device: (
                not device.get("matched_known_type", False),
                not bool(device.get("device_key")),
                not bool(device.get("name")),
            ),
        )

        if manual_key != "AUTO-DETECT":
            for device in ranked_devices:
                normalized_hex_key = (device.get("device_key") or "").upper()
                if normalized_hex_key != manual_key:
                    continue
                candidate = device.get("_device")
                if candidate is None:
                    continue
                device_name = device.get("name") or ""
                dev_type = device.get("device_type")
                self._device = candidate
                self._device_name = "Insight" if (dev_type in {"Insight", "Insight2"} or "insight" in device_name.lower()) else (dev_type or name_filter)
                self._hex_key = normalized_hex_key
                return (self._device_name, self._hex_key)

        for device in ranked_devices:
            device_name = device.get("name") or ""
            dev_type = device.get("device_type")
            hex_key = device.get("device_key")
            normalized_hex_key = hex_key.upper() if isinstance(hex_key, str) else hex_key
            if manual_key != "AUTO-DETECT":
                if normalized_hex_key != manual_key:
                    continue
            else:
                if not self._is_emotiv_candidate(device_name, dev_type, normalized_hex_key):
                    continue
                if name_filter.lower() not in device_name.lower() and dev_type not in {"Insight", "Insight2", "EPOC", "EPOC+"}:
                    continue
            candidate = device.get("_device")
            if candidate is None:
                continue
            self._device = candidate
            self._device_name = "Insight" if (dev_type in {"Insight", "Insight2"} or "insight" in device_name.lower()) else (dev_type or name_filter)
            self._hex_key = normalized_hex_key or ""
            return (self._device_name, self._hex_key)

        diagnostic_summary = [
            {
                "name": device.get("name"),
                "device_type": device.get("device_type"),
                "device_key": device.get("device_key"),
                "address": device.get("address"),
                "rssi": device.get("rssi"),
                "has_name": device.get("has_name"),
                "has_device_key": device.get("has_device_key"),
                "gatt_match": device.get("gatt_match"),
                "probe_error": device.get("probe_error"),
            }
            for device in devices
        ]
        raise RuntimeError(
            f"No BLE device with '{name_filter}' in name found (timeout={timeout}s). "
            "The headset may be advertising without an Insight name, may not expose an 8-digit key in the local name, or macOS/CoreBluetooth may be hiding the name while EMOTIV Launcher is connected. "
            f"Visible BLE candidates: {json.dumps(diagnostic_summary, ensure_ascii=False)}"
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
