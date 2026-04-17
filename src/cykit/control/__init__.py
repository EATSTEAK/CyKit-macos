from __future__ import annotations

from pathlib import Path

from ..exceptions import ControlError, RecordingError
from ..models import DataMode, PathLike


class ClientControl:
    """Runtime control surface for an active ``CyKitClient`` connection."""

    def __init__(self, client: object):
        self._client = client

    def set_data_mode(self, mode: DataMode | int) -> None:
        self._client._set_data_mode(mode)

    def set_format(self, value: int) -> None:
        self._client._set_format(value)

    def set_baseline_mode(self, enabled: bool) -> None:
        self._client._set_baseline_mode(enabled)

    def get_baseline(self) -> tuple[float, ...] | None:
        return self._client._get_baseline()

    def disconnect(self) -> None:
        self._client.close()

    def set_model(self, model: int) -> None:
        self._client._set_model(model)

    def set_mask(self, index: int, values: list[int]) -> None:
        self._client._set_mask(index, values)

    def update_settings(self, value: str) -> None:
        raise ControlError("update_settings is not yet supported by the public adapter")

    def start_recording(self, path: PathLike, *, overwrite: bool = False) -> Path:
        return self._client._start_recording(path, overwrite=overwrite)

    def stop_recording(self) -> None:
        self._client._stop_recording()
