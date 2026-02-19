# -*- coding: utf8 -*-
#
#  CyKIT 4.0 - Cross-platform Example
#  ____________________________________
#  ble_insight.py
#
#  Minimal Insight BLE data collection using bleak + pycryptodomex.
#
"""
Usage:
    python examples/ble_insight.py

Requires:
    pip install bleak pycryptodomex

The script scans for a Bluetooth LE Emotiv Insight device, connects,
subscribes to the DATA GATT characteristic, and prints decoded channel
values to the console.
"""

import sys
import queue
import time
from Cryptodome.Cipher import AES
from cykit.platform_ble import get_ble_backend

DATA_UUID = "81072f41-9f3d-11e3-a9dc-0002a5d5c51b"

# Insight 14-bit channel offsets (bit positions within the decrypted payload)
INSIGHT_OFFSETS = [
    0, 8, 14, 22, 28, 36, 42, 50, 56, 64,
    70, 78, 84, 92, 98, 106, 112, 120, 126, 134,
    140, 148, 154, 162, 168, 176, 182, 190, 196, 204,
    210, 218, 224, 232, 238,
]

tasks = queue.Queue()


def make_insight_key(hex_key):
    """Derive the AES key for Insight Consumer (model 4) from the BLE hex key.

    The hex_key is the 8-character string from the device name
    (e.g. "AABBCCDD" from "Insight AABBCCDD").
    """
    serial = b"\x00" * 12 + bytearray.fromhex(
        hex_key[6:8] + hex_key[4:6] + hex_key[2:4] + hex_key[0:2]
    )
    sn = serial
    k = [sn[-1], 0, sn[-2], 21, sn[-3], 0, sn[-4], 12,
         sn[-3], 0, sn[-2], 68, sn[-1], 0, sn[-2], 88]
    return bytes(bytearray(k))


def convert_epoc_plus(value_1, value_2):
    """Convert raw 16-bit pair to a float microvolt value."""
    return "%.8f" % (
        ((int(value_1) * 0.128205128205129) + 4201.02564096001)
        + ((int(value_2) - 128) * 32.82051289)
    )


def main():
    ble = get_ble_backend()

    print("Scanning for Insight BLE device ...")
    dev_type, hex_key = ble.scan_for_device("Insight", timeout=15.0)
    print(f"Found: {dev_type} {hex_key}")

    print("Connecting ...")
    ble.connect(timeout=15.0)
    print("Connected. Subscribing to notifications ...")

    def on_data(data):
        tasks.put(bytearray(data))

    ble.subscribe_notifications(DATA_UUID, on_data)

    key = make_insight_key(hex_key)
    cipher = AES.new(key, AES.MODE_ECB)
    delimiter = ", "

    print("Streaming Insight EEG data (Ctrl+C to stop):\n")
    try:
        while True:
            if tasks.empty():
                time.sleep(0.005)
                continue

            task = tasks.get()

            # Insight BLE: decrypt first 16 bytes, reassemble with tail bytes
            decrypted = cipher.decrypt(task[0:16])
            sel_decrypt = decrypted[0:1] + decrypted[1:16]
            data = (
                task[19:20]
                + sel_decrypt
                + task[16:17]
                + task[17:18]
                + task[18:19]
            )

            # Decode channels using 14-bit offsets
            packet = ""
            for i in range(1, 16, 2):
                packet += convert_epoc_plus(str(data[i]), str(data[i + 1])) + delimiter
            for i in range(18, len(data), 2):
                packet += convert_epoc_plus(str(data[i]), str(data[i + 1])) + delimiter
            packet = packet[: -len(delimiter)]

            print(packet)

    except KeyboardInterrupt:
        print("\nDisconnecting ...")
        ble.disconnect()
        print("Done.")


if __name__ == "__main__":
    main()
