from __future__ import annotations

import json

import pytest
import typer

from cykit.main import _build_modern_parameters, cli, parse_legacy_config
from cykit.models import DeviceInfo, Model, Transport


def test_parse_legacy_config_bluetooth_noweb() -> None:
    connection, stream, output = parse_legacy_config("bluetooth=AABBCCDD+noweb+format-3+verbose")
    assert connection.device_key == "aabbccdd"
    assert stream.include_header is True
    assert output.format == 3
    assert output.verbose is True


def test_build_modern_parameters_includes_new_flags() -> None:
    parameters = _build_modern_parameters(
        "",
        verbose=True,
        info=False,
        confirm=True,
        noheader=False,
        nocounter=False,
        nobattery=False,
        blankdata=False,
        blankcsv=False,
        outputdata=False,
        outputraw=False,
        generic=False,
        openvibe=False,
        integer=False,
        baseline=False,
        filter_enabled=False,
        allmode=False,
        gyromode=False,
        noweb=True,
        bluetooth_key="AABBCCDD",
        bluetooth_auto=False,
        format_value=3,
        ovdelay=None,
        ovsamples=None,
    )
    assert "verbose" in parameters
    assert "confirm" in parameters
    assert "bluetooth=AABBCCDD" in parameters
    assert "noweb" in parameters
    assert "format-3" in parameters


def test_cli_rejects_invalid_port() -> None:
    exit_code = cli(["run", "127.0.0.1", "10", "4", "--noweb"])
    assert exit_code == 2


def test_cli_accepts_help() -> None:
    exit_code = cli(["--help"])
    assert exit_code == 0


def test_legacy_usage_requires_max_four_arguments() -> None:
    with pytest.raises(typer.BadParameter, match="at most 4 arguments"):
        cli(["127.0.0.1", "54123", "4", "noweb", "extra"])


def test_cli_bluetooth_autodetect_failure_returns_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cykit.main._run_once",
        lambda config: (_ for _ in ()).throw(RuntimeError("Bluetooth device discovery failed")),
    )
    exit_code = cli(["run", "127.0.0.1", "54123", "4", "--bluetooth", "--noweb"])
    assert exit_code == 1


def test_discover_json_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "cykit.main.discover_devices",
        lambda transport, timeout, probe_gatt, probe_timeout: [
            DeviceInfo(
                name="Insight2 (AABBCCDD)",
                device_key="AABBCCDD",
                transport=Transport.BLUETOOTH,
                model_guess=Model.INSIGHT_CONSUMER,
                address="00:11:22:33",
                rssi=-55,
                metadata={"raw_name": "Insight2 (AABBCCDD)", "has_name": True, "gatt_match": True},
            )
        ],
    )
    exit_code = cli(["discover", "--transport", "bluetooth", "--json"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["name"] == "Insight2 (AABBCCDD)"
    assert payload[0]["transport"] == "bluetooth"


def test_discover_text_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "cykit.main.discover_devices",
        lambda transport, timeout, probe_gatt, probe_timeout: [
            DeviceInfo(
                name="Insight2 (AABBCCDD)",
                device_key="AABBCCDD",
                transport=Transport.BLUETOOTH,
                model_guess=Model.INSIGHT_CONSUMER,
                address="00:11:22:33",
                rssi=-55,
                metadata={
                    "raw_name": "Insight2 (AABBCCDD)",
                    "has_name": True,
                    "gatt_match": True,
                    "gatt_services": ["81072f41-9f3d-11e3-a9dc-0002a5d5c51b"],
                    "probe_error": None,
                },
            )
        ],
    )
    exit_code = cli(["discover", "--transport", "bluetooth"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Insight2 (AABBCCDD)" in output
    assert "device_key=AABBCCDD" in output
    assert "gatt_match" in output
