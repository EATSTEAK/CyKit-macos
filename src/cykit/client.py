from __future__ import annotations

import queue
import time
from pathlib import Path
from typing import Iterator

from Cryptodome.Cipher import AES

from . import eeg
from ._helpers import convert_epoc_plus_value, derive_key, model_channel_names, normalize_model, utc_now
from .control import ClientControl
from .discovery import discover
from .exceptions import ConnectionError, ControlError, RecordingError, StreamError
from .models import ConnectionOptions, DataMode, DeviceInfo, Model, OutputOptions, PathLike, Sample, StreamOptions, Transport


class CyKitClient:
    """Public synchronous client for CyKit device discovery, streaming, and control.

    Args:
        model: Target headset model.
        connection: Transport and discovery settings.
        stream: Stream formatting and runtime behavior options.
        output: Output normalization and compatibility options.

    Raises:
        ConnectionError: If the client cannot initialize the selected transport.
    """

    def __init__(
        self,
        model: Model | int,
        *,
        connection: ConnectionOptions = ConnectionOptions(),
        stream: StreamOptions = StreamOptions(),
        output: OutputOptions = OutputOptions(),
    ) -> None:
        self.model = normalize_model(model)
        self.connection = connection
        self.stream = stream
        self.output = output
        self.control = ClientControl(self)
        self._connected = False
        self._device_info: DeviceInfo | None = None
        self._eeg: eeg.EEG | None = None
        self._io: eeg.ControllerIO | None = None
        self._cipher = None
        self._delimiter = ", "
        self._recording_path: Path | None = None

    def __enter__(self) -> "CyKitClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._device_info

    @property
    def io(self) -> eeg.ControllerIO | None:
        return self._io

    def connect(self) -> None:
        """Connect to the configured device and prepare streaming.

        Raises:
            ConnectionError: If no compatible device can be prepared.
        """
        if self._connected:
            return

        config = self._build_legacy_config()
        try:
            eeg.configure_runtime(config)
            self._io = eeg.ControllerIO()
            self._io.setInfo("ioObject", self._io)
            self._io.setInfo("config", config)
            self._io.setInfo("verbose", str(self.output.verbose))
            self._io.setInfo("noweb", "True")
            self._io.setInfo("status", "True")
            self._io.setInfo("DeviceObject", object())
            self._eeg = eeg.EEG(int(self.model), self._io, config)
            serial_bytes = self._resolve_serial_bytes()
            self._cipher = AES.new(derive_key(serial_bytes, self.model), AES.MODE_ECB)
            self._device_info = self._resolve_device_info()
            self._connected = True
        except Exception as exc:
            self.close()
            raise ConnectionError(str(exc)) from exc

    def close(self) -> None:
        """Close the active connection and release runtime state."""
        if self._io is not None:
            self._io.setInfo("status", "False")
            try:
                if self._io.isRecording():
                    self._io.stopRecord()
            except Exception:
                pass
        if eeg.eeg_driver == "bluetooth":
            backend = getattr(eeg, "_ble_backend", None)
            if backend is not None:
                try:
                    backend.disconnect()
                except Exception:
                    pass
        self._connected = False

    def attach_server(self, server: object) -> None:
        if self._io is None:
            raise ConnectionError("Client is not connected")
        self._io.setServer(server)

    def start_background_stream(self) -> None:
        if not self._connected or self._eeg is None or self._io is None:
            raise StreamError("Client is not connected")
        self._eeg.start()

    def handle_legacy_command(self, text: str) -> object:
        if not text.startswith("CyKITv2:::"):
            if self._io is None:
                raise ControlError("Client is not connected")
            return self._io.onData(1, text)

        parts = text.split(":::")
        command = parts[1] if len(parts) > 1 else ""
        args = parts[2:]

        if command == "setDataMode" and args:
            self.control.set_data_mode(int(args[0]))
            return None
        if command == "changeFormat" and args:
            self.control.set_format(int(args[0]))
            return None
        if command == "setBaselineMode" and args:
            self.control.set_baseline_mode(args[0] == "1")
            return None
        if command == "getBaseline":
            return self.control.get_baseline()
        if command == "RecordStart" and args:
            return self.control.start_recording(args[0])
        if command == "RecordStop":
            self.control.stop_recording()
            return None
        if command == "Disconnect":
            self.close()
            return None
        if command == "setModel" and args:
            self.control.set_model(int(args[0]))
            return None
        if command == "setMask" and len(args) >= 2:
            self.control.set_mask(int(args[0]), [int(value) for value in args[1].split(",") if value])
            return None
        if self._io is None:
            raise ControlError("Client is not connected")
        return self._io.onData(1, text)

    def stream(self) -> Iterator[Sample]:
        """Yield decoded EEG samples until the caller stops or the client closes.

        Yields:
            Structured sample objects with float-normalized EEG values.

        Raises:
            StreamError: If streaming has not been initialized or decoding fails.
        """
        if not self._connected or self._eeg is None or self._io is None or self._cipher is None:
            raise StreamError("Client is not connected")

        if eeg.tasks.empty():
            try:
                eeg.tasks.queue.clear()
            except Exception:
                pass

        while self._connected:
            if eeg.tasks.empty():
                time.sleep(0.005)
                continue
            task = eeg.tasks.get()
            try:
                sample = self._decode_task(task)
            except Exception as exc:
                raise StreamError(str(exc)) from exc
            if sample is None:
                continue
            yield sample

    def _resolve_serial_bytes(self) -> bytes:
        if self._eeg is None:
            raise ConnectionError("EEG state is unavailable")
        serial = self._eeg.serial_number
        if isinstance(serial, str):
            return bytes(ord(char) for char in serial)
        return bytes(serial)

    def _resolve_device_info(self) -> DeviceInfo:
        if self.connection.transport == Transport.BLUETOOTH:
            matches = discover(transport=Transport.BLUETOOTH, timeout=self.connection.scan_timeout)
            if self.connection.device_key:
                for device in matches:
                    if device.device_key == self.connection.device_key:
                        return device
            if matches:
                return matches[0]
        matches = discover(transport=Transport.USB if self.connection.transport == Transport.USB else Transport.AUTO, timeout=self.connection.scan_timeout)
        if matches:
            return matches[0]
        return DeviceInfo(name="Unknown", device_key=self.connection.device_key, transport=self.connection.transport)

    def _build_legacy_config(self) -> str:
        parts: list[str] = ["noweb"]
        if self.connection.transport == Transport.BLUETOOTH:
            key = self.connection.device_key
            parts.append(f"bluetooth={key}" if key else "bluetooth")
        if self.output.verbose:
            parts.append("verbose")
        if not self.stream.include_header:
            parts.append("noheader")
        if self.output.no_counter:
            parts.append("nocounter")
        if self.output.no_battery:
            parts.append("nobattery")
        if self.output.integer_values:
            parts.append("integer")
        if self.output.blank_data:
            parts.append("blankdata")
        if self.output.blank_csv:
            parts.append("blankcsv")
        if self.output.output_data:
            parts.append("outputdata")
        if self.output.output_raw:
            parts.append("outputraw")
        if self.stream.baseline:
            parts.append("baseline")
        if self.stream.filter_enabled:
            parts.append("filter")
        if self.stream.openvibe:
            parts.append("openvibe")
            parts.append(f"ovdelay:{self.stream.openvibe_delay:03d}")
            parts.append(f"ovsamples:{self.stream.openvibe_samples:03d}")
        parts.append(f"format-{self.output.format}")
        parts.append(f"delimiter={ord(self._delimiter)}")
        if self.stream.data_mode == DataMode.ALL:
            parts.append("allmode")
        elif self.stream.data_mode == DataMode.GYRO:
            parts.append("gyromode")
        else:
            parts.append("eegmode")
        return "+".join(parts)

    def _decode_task(self, task: object) -> Sample | None:
        if self._eeg is None:
            raise StreamError("EEG state is unavailable")

        raw_bytes = bytes(task)
        payload = self._decrypt_payload(raw_bytes)
        if payload is None:
            return None

        if self.model in {Model.EPOC_PLUS_PREMIUM, Model.EPOC_PLUS_CONSUMER}:
            return self._decode_epoc_plus_sample(payload, raw_bytes)
        if self.model in {Model.INSIGHT_PREMIUM, Model.INSIGHT_CONSUMER, Model.EPOC_PLUS_STANDARD}:
            return self._decode_insight_sample(payload, raw_bytes)
        return self._decode_epoc_sample(payload, raw_bytes)

    def _decrypt_payload(self, raw_bytes: bytes) -> bytes | None:
        if self._cipher is None:
            raise StreamError("Cipher is unavailable")
        if eeg.eeg_driver == "bluetooth":
            if getattr(eeg, "BTLE_device_name", "") == "Insight":
                decrypted = self._cipher.decrypt(raw_bytes[0:16])
                return raw_bytes[19:20] + decrypted[0:1] + decrypted[1:16] + raw_bytes[16:17] + raw_bytes[17:18] + raw_bytes[18:19]
            if len(raw_bytes) == 32:
                return self._cipher.decrypt(raw_bytes)
            return self._cipher.decrypt(raw_bytes[0:16]) + self._cipher.decrypt(raw_bytes[16:32])
        return self._cipher.decrypt(raw_bytes)

    def _decode_epoc_plus_sample(self, data: bytes, raw_bytes: bytes) -> Sample | None:
        if len(data) < 18:
            return None
        packet_kind = int(data[1])
        if packet_kind == 16 and self.stream.data_mode == DataMode.GYRO:
            return None
        if packet_kind == 32 and self.stream.data_mode == DataMode.EEG:
            return None

        names = model_channel_names(self.model)
        eeg_values: dict[str, float] = {}
        value_index = 0
        for index in range(2, 16, 2):
            eeg_values[names[value_index]] = convert_epoc_plus_value(data[index], data[index + 1])
            value_index += 1
        for index in range(18, len(data), 2):
            if value_index >= len(names):
                break
            eeg_values[names[value_index]] = convert_epoc_plus_value(data[index], data[index + 1])
            value_index += 1

        battery = None if self.output.no_battery else int(data[16])
        quality = None if self.output.no_battery else int(data[17])
        raw = raw_bytes if self.stream.include_raw else None
        return Sample(
            captured_at=utc_now(),
            eeg=eeg_values,
            counter=int(data[0]) if not self.output.no_counter else None,
            packet_kind=packet_kind,
            battery=battery,
            quality=quality,
            raw=raw,
        )

    def _decode_insight_sample(self, data: bytes, raw_bytes: bytes) -> Sample:
        names = model_channel_names(Model.INSIGHT_CONSUMER)
        eeg_values: dict[str, float] = {}
        value_index = 0
        for index in range(1, 16, 2):
            eeg_values[names[value_index]] = convert_epoc_plus_value(data[index], data[index + 1])
            value_index += 1
        for index in range(18, len(data), 2):
            if value_index >= len(names):
                break
            eeg_values[names[value_index]] = convert_epoc_plus_value(data[index], data[index + 1])
            value_index += 1

        battery = None if self.output.no_battery or len(data) < 18 else int(data[16])
        quality = None if self.output.no_battery or len(data) < 18 else int(data[17])
        raw = raw_bytes if self.stream.include_raw else None
        return Sample(
            captured_at=utc_now(),
            eeg=eeg_values,
            counter=int(data[0]) if not self.output.no_counter else None,
            battery=battery,
            quality=quality,
            raw=raw,
        )

    def _decode_epoc_sample(self, data: bytes, raw_bytes: bytes) -> Sample:
        if self._eeg is None:
            raise StreamError("EEG state is unavailable")
        names = model_channel_names(self.model)
        eeg_values = {
            names[index]: float(self._eeg.convertEPOC(data[1:], self._eeg.mask[index]))
            for index in range(len(names))
        }
        raw = raw_bytes if self.stream.include_raw else None
        return Sample(
            captured_at=utc_now(),
            eeg=eeg_values,
            counter=int(data[0]) if not self.output.no_counter else None,
            raw=raw,
        )

    def _set_data_mode(self, mode: DataMode | int) -> None:
        self.stream = StreamOptions(
            data_mode=DataMode(int(mode)),
            include_header=self.stream.include_header,
            include_raw=self.stream.include_raw,
            delimiter=self.stream.delimiter,
            baseline=self.stream.baseline,
            filter_enabled=self.stream.filter_enabled,
            openvibe=self.stream.openvibe,
            openvibe_delay=self.stream.openvibe_delay,
            openvibe_samples=self.stream.openvibe_samples,
        )
        if self._io is not None:
            self._io.datamode = int(mode)
            self._io.setInfo("datamode", str(int(mode)))

    def _set_format(self, value: int) -> None:
        self.output = OutputOptions(
            format=value,
            integer_values=self.output.integer_values,
            no_counter=self.output.no_counter,
            no_battery=self.output.no_battery,
            blank_data=self.output.blank_data,
            blank_csv=self.output.blank_csv,
            verbose=self.output.verbose,
            output_data=self.output.output_data,
            output_raw=self.output.output_raw,
        )
        if self._io is not None:
            self._io.format = value
            self._io.setInfo("format", str(value))

    def _set_baseline_mode(self, enabled: bool) -> None:
        self.stream = StreamOptions(
            data_mode=self.stream.data_mode,
            include_header=self.stream.include_header,
            include_raw=self.stream.include_raw,
            delimiter=self.stream.delimiter,
            baseline=enabled,
            filter_enabled=self.stream.filter_enabled,
            openvibe=self.stream.openvibe,
            openvibe_delay=self.stream.openvibe_delay,
            openvibe_samples=self.stream.openvibe_samples,
        )
        if self._io is not None:
            self._io.setBaselineMode(enabled)

    def _get_baseline(self) -> tuple[float, ...] | None:
        if self._io is None:
            return None
        baseline = self._io.getBaseline()
        if baseline is None:
            return None
        return tuple(float(value) for value in baseline)

    def _set_model(self, model: int) -> None:
        self.model = normalize_model(model)
        if self._io is not None:
            self._io.newModel = int(self.model)

    def _set_mask(self, index: int, values: list[int]) -> None:
        if self._io is None:
            raise StreamError("Client is not connected")
        self._io.newMask = index
        self._io.setMask[index] = values

    def _start_recording(self, path: PathLike, *, overwrite: bool = False) -> Path:
        if self._io is None:
            raise RecordingError("Client is not connected")
        target = Path(path)
        if not target.suffix:
            target = Path.cwd() / target.name
            target = target.with_suffix(".csv")
        elif not target.is_absolute():
            target = Path.cwd() / target
        if target.exists() and not overwrite:
            raise RecordingError(f"Recording target already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and overwrite:
            target.unlink()
        self._io.recordFile = target.stem
        self._io.recordInc = 0
        self._io.cyFile = open(target, "w+", newline="")
        self._io.setInfo("recording", "True")
        self._io.packet_count = 0
        self._recording_path = target
        return target

    def _stop_recording(self) -> None:
        if self._io is None:
            raise RecordingError("Client is not connected")
        self._io.stopRecord()
