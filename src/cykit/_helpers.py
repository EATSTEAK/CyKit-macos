from __future__ import annotations

from datetime import datetime, timezone

from .models import Model

EPOC_CHANNEL_NAMES = [
    "F3",
    "FC5",
    "AF3",
    "F7",
    "T7",
    "P7",
    "O1",
    "O2",
    "P8",
    "T8",
    "F8",
    "AF4",
    "FC6",
    "F4",
]

INSIGHT_CHANNEL_NAMES = ["AF3", "T7", "Pz", "T8", "AF4"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_model(model: Model | int) -> Model:
    if isinstance(model, Model):
        return model
    return Model(int(model))


def model_channel_names(model: Model) -> list[str]:
    if model in {Model.INSIGHT_PREMIUM, Model.INSIGHT_CONSUMER}:
        return INSIGHT_CHANNEL_NAMES.copy()
    return EPOC_CHANNEL_NAMES.copy()


def derive_key(serial_bytes: bytes, model: Model) -> bytes:
    sn = bytearray(serial_bytes)
    if len(sn) != 16:
        raise ValueError("serial_bytes must be 16 bytes long")

    if model == Model.EPOC_PREMIUM:
        key = [sn[-1], 0, sn[-2], 72, sn[-1], 0, sn[-2], 84, sn[-3], 16, sn[-4], 66, sn[-3], 0, sn[-4], 80]
    elif model == Model.EPOC_CONSUMER:
        key = [sn[-1], 0, sn[-2], 84, sn[-3], 16, sn[-4], 66, sn[-1], 0, sn[-2], 72, sn[-3], 0, sn[-4], 80]
    elif model == Model.INSIGHT_PREMIUM:
        key = [sn[-2], 0, sn[-1], 68, sn[-2], 0, sn[-1], 12, sn[-4], 0, sn[-3], 21, sn[-4], 0, sn[-3], 88]
    elif model == Model.INSIGHT_CONSUMER:
        key = [sn[-1], 0, sn[-2], 21, sn[-3], 0, sn[-4], 12, sn[-3], 0, sn[-2], 68, sn[-1], 0, sn[-2], 88]
    elif model == Model.EPOC_PLUS_PREMIUM:
        key = [sn[-2], sn[-1], sn[-2], sn[-1], sn[-3], sn[-4], sn[-3], sn[-4], sn[-4], sn[-3], sn[-4], sn[-3], sn[-1], sn[-2], sn[-1], sn[-2]]
    elif model == Model.EPOC_PLUS_CONSUMER:
        key = [sn[-1], sn[-2], sn[-2], sn[-3], sn[-3], sn[-3], sn[-2], sn[-4], sn[-1], sn[-4], sn[-2], sn[-2], sn[-4], sn[-4], sn[-2], sn[-1]]
    elif model == Model.EPOC_PLUS_STANDARD:
        key = [sn[-1], 0, sn[-2], 21, sn[-3], 0, sn[-4], 12, sn[-3], 0, sn[-2], 68, sn[-1], 0, sn[-2], 88]
    else:
        raise ValueError(f"Unsupported model: {model}")
    return bytes(bytearray(key))


def convert_epoc_value(data: bytes, bits: list[int]) -> float:
    level = 0
    for index in range(13, -1, -1):
        level <<= 1
        byte_index = int(bits[index] / 8)
        offset = bits[index] % 8
        level |= (data[byte_index] >> offset) & 1
    return float(level)


def convert_epoc_plus_value(value_1: int | str, value_2: int | str) -> float:
    return float(
        ((int(value_1) * 0.128205128205129) + 4201.02564096001)
        + ((int(value_2) - 128) * 32.82051289)
    )
