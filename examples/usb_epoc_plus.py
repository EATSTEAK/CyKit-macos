# -*- coding: utf8 -*-
#
#  CyKIT 4.0 - Cross-platform Example
#  ____________________________________
#  usb_epoc_plus.py
#
#  Minimal EPOC+ USB data collection using pyusb + pycryptodomex.
#
"""
Usage:
    python examples/usb_epoc_plus.py

Requires:
    pip install pyusb pycryptodomex

On macOS / Linux you may also need libusb installed:
    brew install libusb          # macOS
    sudo apt install libusb-1.0  # Debian/Ubuntu
"""

import sys
import queue
import usb.core
import usb.util
import usb.backend.libusb1
from Cryptodome.Cipher import AES

tasks = queue.Queue()


def find_emotiv_device():
    """Find and return the first Emotiv EEG USB device."""
    backend = usb.backend.libusb1.get_backend()
    if backend is None:
        print("libusb backend not found. Install libusb.")
        sys.exit(1)

    devices = usb.core.find(find_all=True, backend=backend)
    known_names = ["EPOC+", "EEG Signals", "Emotiv RAW DATA", "FLEX"]

    for dev in devices:
        try:
            product = usb.util.get_string(dev, dev.iProduct)
        except Exception:
            continue
        if product in known_names:
            return dev, product

    print("No Emotiv USB device found.")
    sys.exit(1)


def make_key(serial_number, model=6):
    """Derive the AES key from the device serial number.

    model=6: EPOC+ Consumer 16-bit (default)
    model=5: EPOC+ Premium 16-bit
    """
    sn = bytearray(ord(c) for c in serial_number)

    if model == 6:
        k = [sn[-1], sn[-2], sn[-2], sn[-3], sn[-3], sn[-3], sn[-2], sn[-4],
             sn[-1], sn[-4], sn[-2], sn[-2], sn[-4], sn[-4], sn[-2], sn[-1]]
    elif model == 5:
        k = [sn[-2], sn[-1], sn[-2], sn[-1], sn[-3], sn[-4], sn[-3], sn[-4],
             sn[-4], sn[-3], sn[-4], sn[-3], sn[-1], sn[-2], sn[-1], sn[-2]]
    else:
        raise ValueError(f"Unsupported model: {model}")

    return bytes(bytearray(k))


def convert_epoc_plus(value_1, value_2):
    """Convert raw EPOC+ 16-bit pair to a float microvolt value."""
    return "%.8f" % (
        ((int(value_1) * 0.128205128205129) + 4201.02564096001)
        + ((int(value_2) - 128) * 32.82051289)
    )


def main():
    device, product_name = find_emotiv_device()
    print(f"Found: {product_name}")

    device.set_configuration()
    serial = usb.util.get_string(device, device.iSerialNumber)
    print(f"Serial: {serial}")

    key = make_key(serial, model=6)
    cipher = AES.new(key, AES.MODE_ECB)
    delimiter = ", "

    print("Streaming EEG data (Ctrl+C to stop):\n")
    try:
        while True:
            try:
                raw = device.read(0x82, 32, 100)
            except Exception as e:
                if getattr(e, "errno", None) == 10060:
                    continue
                raise

            data = cipher.decrypt(raw.tobytes())

            # Skip gyro-only packets
            if str(data[1]) == "32":
                continue

            packet = ""
            for i in range(2, 16, 2):
                packet += convert_epoc_plus(str(data[i]), str(data[i + 1])) + delimiter
            for i in range(18, len(data), 2):
                packet += convert_epoc_plus(str(data[i]), str(data[i + 1])) + delimiter
            packet = packet[: -len(delimiter)]

            print(packet)

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
