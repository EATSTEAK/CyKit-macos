from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from pathlib import Path
from typing import Mapping


class Model(IntEnum):
    EPOC_PREMIUM = 1
    EPOC_CONSUMER = 2
    INSIGHT_PREMIUM = 3
    INSIGHT_CONSUMER = 4
    EPOC_PLUS_PREMIUM = 5
    EPOC_PLUS_CONSUMER = 6
    EPOC_PLUS_STANDARD = 7


class Transport(str, Enum):
    AUTO = "auto"
    BLUETOOTH = "bluetooth"
    USB = "usb"


class DataMode(IntEnum):
    ALL = 0
    EEG = 1
    GYRO = 2


@dataclass(frozen=True)
class ConnectionOptions:
    transport: Transport = Transport.AUTO
    device_key: str | None = None
    scan_timeout: float = 15.0
    connect_timeout: float = 15.0
    confirm_device: bool = False


@dataclass(frozen=True)
class StreamOptions:
    data_mode: DataMode = DataMode.EEG
    include_header: bool = True
    include_raw: bool = False
    delimiter: str = ","
    baseline: bool = False
    filter_enabled: bool = False
    openvibe: bool = False
    openvibe_delay: int = 100
    openvibe_samples: int = 4


@dataclass(frozen=True)
class OutputOptions:
    format: int = 0
    integer_values: bool = False
    no_counter: bool = False
    no_battery: bool = False
    blank_data: bool = False
    blank_csv: bool = False
    verbose: bool = False
    output_data: bool = False
    output_raw: bool = False


@dataclass(frozen=True)
class DeviceInfo:
    name: str
    device_key: str | None
    transport: Transport
    model_guess: Model | None = None
    serial: str | None = None
    address: str | None = None
    rssi: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Sample:
    captured_at: datetime
    eeg: Mapping[str, float]
    counter: int | None = None
    packet_kind: int | None = None
    gyro: tuple[float, float] | None = None
    battery: int | None = None
    quality: int | None = None
    raw: bytes | str | None = None


PathLike = str | Path
