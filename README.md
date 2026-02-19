<img src="https://raw.githubusercontent.com/CymatiCorp/CyKit/git-images/Images/CyKIT5.png" width=34% height=34%  />

# CyKIT 4.0 -- Cross-platform Emotiv EEG

CyKIT is an open-source data acquisition tool for Emotiv EEG headsets (Epoc, Insight, Epoc+).
It runs on **macOS, Linux, and Windows** with Python 3.10+.

## Installation

```bash
pip install -e .
# or with uv:
uv pip install -e .
```

### Dependencies

| Package         | Purpose                      |
| --------------- | ---------------------------- |
| `pycryptodomex` | AES decryption of EEG data   |
| `bleak`         | Bluetooth LE (macOS / Linux) |
| `pyusb`         | USB communication via libusb |

On macOS you may also need:

```bash
brew install libusb
```

## Quick Start

```bash
# CLI entry point
cykit 127.0.0.1 54123 6 noweb

# or via python -m
python -m cykit 127.0.0.1 54123 6 noweb

# help
cykit --help
```

### Supported Models

| #   | Headset            | Mode           |
| --- | ------------------ | -------------- |
| 1   | Epoc (Premium)     | 14-bit, 128 Hz |
| 2   | Epoc (Consumer)    | 14-bit, 128 Hz |
| 3   | Insight (Premium)  | 128 Hz         |
| 4   | Insight (Consumer) | 128 Hz         |
| 5   | Epoc+ (Premium)    | 16-bit, 256 Hz |
| 6   | Epoc+ (Consumer)   | 16-bit, 256 Hz |
| 7   | Epoc+ (Consumer)   | 14-bit, 128 Hz |

### Bluetooth LE

```bash
# Auto-detect paired device
cykit 127.0.0.1 54123 4 bluetooth+noweb

# Specify 8-hex-digit key from device name
cykit 127.0.0.1 54123 4 bluetooth=AABBCCDD+noweb
```

## Project Structure

```
CyKit/
├── src/cykit/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py          # CLI entry point
│   ├── eeg.py           # EEG data acquisition & processing
│   ├── websocket.py     # WebSocket / TCP server
│   └── platform_ble/    # Bluetooth LE (bleak)
│       ├── __init__.py
│       ├── base.py
│       └── bleak_backend.py
├── examples/
│   ├── usb_epoc_plus.py
│   └── ble_insight.py
├── Web/                 # Browser interface
├── pyproject.toml
└── README.md
```

## Headset Support

Does not currently work with Epoc-X.
See Discord for details about Flex.

## Browser Interface

<img src="https://raw.githubusercontent.com/CymatiCorp/CyKit/git-images/Images/CyKIT-Preview.png" />

## Documentation

- [CyKIT 3.0 (wikipage)](https://github.com/CymatiCorp/CyKit/wiki/CyKIT-3.0-Documentation)
- [How to Install CyKIT](https://github.com/CymatiCorp/CyKit/wiki/How-to-Install-CyKIT)
- [How to Stream Data to OpenViBE](https://github.com/CymatiCorp/CyKit/wiki/How-to-Stream-Data-to-OpenViBE)
- [How to Pair USB device](https://github.com/CymatiCorp/CyKit/wiki/How-to-Pair-USB-device)
- [How to Change EPOC+ hertz modes](<https://github.com/CymatiCorp/CyKit/wiki//How-to-Change-EPOC(plus)--modes>)

## Communication

Chat Discussion: https://discordapp.com/invite/gTYNWc7

## Version History

```
CyKIT v1.0 python 2.7.6 (2014)
CyKIT v1.0 python 3.3.x (2015)
CyKIT v2.0 Python 2.7.6 (2018.Jan.29)
CyKIT v3.0 Python 3.x   (2018.Dec.26)
CyKIT v3.1 Python 3.10+  (2024)
```

## Documentation

[Bluetooth Development Documentation](https://github.com/CymatiCorp/CyKit/blob/git-images/Documentation/Bluetooth_Development-Epoc.pdf)
