from __future__ import annotations

from typing import Iterable

from .exceptions import DiscoveryError
from .models import DeviceInfo, Model, Transport
from .platform_ble import get_ble_backend

USB_KNOWN_NAMES = {
    "EPOC+": None,
    "EEG Signals": None,
    "Emotiv RAW DATA": None,
    "FLEX": None,
}

BLUETOOTH_MODEL_GUESSES = {
    "Insight": Model.INSIGHT_CONSUMER,
    "Insight2": Model.INSIGHT_CONSUMER,
    "EPOC": Model.EPOC_PLUS_CONSUMER,
    "EPOC+": Model.EPOC_PLUS_CONSUMER,
}


def _discover_usb_devices() -> list[DeviceInfo]:
    try:
        import usb.backend.libusb1
        import usb.core
        import usb.util
    except ImportError as exc:
        raise DiscoveryError("USB discovery requires pyusb and libusb support") from exc

    backend = usb.backend.libusb1.get_backend()
    if backend is None:
        raise DiscoveryError("libusb backend not found")

    devices: Iterable[object] = usb.core.find(find_all=True, backend=backend) or []
    results: list[DeviceInfo] = []

    for device in devices:
        try:
            name = usb.util.get_string(device, device.iProduct)
        except Exception:
            continue
        if name not in USB_KNOWN_NAMES:
            continue

        try:
            serial = usb.util.get_string(device, device.iSerialNumber)
        except Exception:
            serial = None

        results.append(
            DeviceInfo(
                name=name,
                device_key=None,
                transport=Transport.USB,
                model_guess=BLUETOOTH_MODEL_GUESSES.get(name),
                serial=serial,
                metadata={
                    "vendor_id": getattr(device, "idVendor", None),
                    "product_id": getattr(device, "idProduct", None),
                },
            )
        )
    return results


def _discover_bluetooth_devices(timeout: float, *, probe_gatt: bool = True, probe_timeout: float = 2.0) -> list[DeviceInfo]:
    backend = get_ble_backend()
    try:
        devices = backend.discover_devices(timeout=timeout, probe_gatt=probe_gatt, probe_timeout=probe_timeout)
    except AttributeError as exc:
        raise DiscoveryError("Active BLE backend does not support device discovery") from exc
    except Exception as exc:
        raise DiscoveryError(str(exc)) from exc

    results: list[DeviceInfo] = []
    for device in devices:
        results.append(
            DeviceInfo(
                name=device.get("name") or "Unknown",
                device_key=device.get("device_key"),
                transport=Transport.BLUETOOTH,
                model_guess=BLUETOOTH_MODEL_GUESSES.get(device.get("device_type", "")) or (Model.INSIGHT_CONSUMER if device.get("gatt_match") and "insight" in (device.get("name") or "").lower() else None),
                serial=device.get("serial"),
                address=device.get("address"),
                rssi=device.get("rssi"),
                metadata=device,
            )
        )
    return results


def discover(*, transport: Transport = Transport.AUTO, timeout: float = 15.0, probe_gatt: bool = True, probe_timeout: float = 2.0) -> list[DeviceInfo]:
    """Discover available CyKit-compatible devices.

    Args:
        transport: Preferred transport. Use ``Transport.AUTO`` to search all supported transports.
        timeout: Scan timeout in seconds for transport layers that need active discovery.

    Returns:
        A list of discovered devices.

    Raises:
        DiscoveryError: If the requested transport cannot be queried.
    """
    results: list[DeviceInfo] = []
    errors: list[Exception] = []

    if transport in {Transport.AUTO, Transport.USB}:
        try:
            results.extend(_discover_usb_devices())
        except Exception as exc:
            errors.append(exc)
            if transport == Transport.USB:
                raise

    if transport in {Transport.AUTO, Transport.BLUETOOTH}:
        try:
            results.extend(_discover_bluetooth_devices(timeout, probe_gatt=probe_gatt, probe_timeout=probe_timeout))
        except Exception as exc:
            errors.append(exc)
            if transport == Transport.BLUETOOTH:
                raise

    if results:
        return results
    if errors and transport != Transport.AUTO:
        first = errors[0]
        if isinstance(first, DiscoveryError):
            raise first
        raise DiscoveryError(str(first)) from first
    return []
