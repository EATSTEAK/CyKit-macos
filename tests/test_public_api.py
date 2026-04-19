from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from cykit import (
    CyKitClient,
    DataMode,
    DeviceInfo,
    Model,
    Sample,
    Transport,
    discover,
)
from cykit.exceptions import ConnectionError, RecordingError


def test_root_public_import_surface() -> None:
    client = CyKitClient(Model.EPOC_PLUS_CONSUMER)
    assert isinstance(client, CyKitClient)
    assert client.model == Model.EPOC_PLUS_CONSUMER


def test_discover_returns_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cykit.discovery._discover_usb_devices",
        lambda: [DeviceInfo(name="EPOC+", device_key=None, transport=Transport.USB)],
    )
    monkeypatch.setattr("cykit.discovery._discover_bluetooth_devices", lambda timeout: [])
    devices = discover()
    assert isinstance(devices, list)
    assert isinstance(devices[0], DeviceInfo)


def test_sample_contract_is_typed() -> None:
    sample = Sample(captured_at=datetime.now(), eeg={"AF3": 1.0}, counter=1)
    assert isinstance(sample.eeg["AF3"], float)
    assert sample.counter == 1


def test_client_control_updates_stream_options() -> None:
    client = CyKitClient(Model.INSIGHT_CONSUMER)
    client.control.set_data_mode(DataMode.GYRO)
    assert client.stream_options.data_mode == DataMode.GYRO


def test_recording_path_requires_connection(tmp_path: Path) -> None:
    client = CyKitClient(Model.EPOC_PLUS_CONSUMER)
    with pytest.raises(RecordingError):
        client.control.start_recording(tmp_path / "session.csv")


def test_recording_rejects_existing_file(tmp_path: Path) -> None:
    client = CyKitClient(Model.EPOC_PLUS_CONSUMER)

    class DummyIO:
        def __init__(self) -> None:
            self.recordFile = ""
            self.recordInc = 0
            self.cyFile = None
            self.info = {}

        def setInfo(self, key: str, value: str) -> None:
            self.info[key] = value

        def stopRecord(self) -> None:
            return None

    client._io = DummyIO()
    existing = tmp_path / "session.csv"
    existing.write_text("x")

    with pytest.raises(RecordingError):
        client.control.start_recording(existing)


def test_path_only_name_uses_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = CyKitClient(Model.EPOC_PLUS_CONSUMER)

    class DummyIO:
        def __init__(self) -> None:
            self.recordFile = ""
            self.recordInc = 0
            self.cyFile = None
            self.info = {}

        def setInfo(self, key: str, value: str) -> None:
            self.info[key] = value

        def stopRecord(self) -> None:
            return None

    client._io = DummyIO()
    monkeypatch.chdir(tmp_path)
    target = client.control.start_recording("session")
    assert target == tmp_path / "session.csv"
    client.control.stop_recording()


def test_connect_rejects_invalid_serial_length(monkeypatch: pytest.MonkeyPatch) -> None:
    client = CyKitClient(Model.INSIGHT_CONSUMER)

    class DummyIO:
        def __init__(self) -> None:
            self.info = {}

        def setInfo(self, key: str, value: str) -> None:
            self.info[key] = value

        def getInfo(self, key: str) -> str:
            return self.info.get(key, "0")

        def isRecording(self) -> bool:
            return False

        def stopRecord(self) -> None:
            return None

    class DummyEEG:
        serial_number = b"short"

    monkeypatch.setattr("cykit.client.eeg.configure_runtime", lambda config: None)
    monkeypatch.setattr("cykit.client.eeg.ControllerIO", DummyIO)
    monkeypatch.setattr("cykit.client.eeg.EEG", lambda model, io, config: DummyEEG())

    with pytest.raises(ConnectionError, match="16-byte serial"):
        client.connect()
