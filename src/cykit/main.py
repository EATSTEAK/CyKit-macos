from __future__ import annotations

import json
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from typing import Annotated

import typer

from cykit import websocket
from cykit.client import CyKitClient
from cykit.discovery import discover as discover_devices
from cykit.exceptions import ConnectionError
from cykit.models import (
    ConnectionOptions,
    DeviceInfo,
    Model,
    OutputOptions,
    StreamOptions,
    Transport,
)

app = typer.Typer(add_completion=False, help="CyKit CLI")

HELP_TEXT = """
CyKIT 4.0

Legacy usage:
  cykit <IP> <Port> <Model#(1-7)> [config]

Modern usage:
  cykit run <IP> <Port> <Model#(1-7)> [OPTIONS]

Legacy config tokens:
  info, confirm, verbose, nocounter, noheader, format-0, format-1, format-3,
  outputdata, outputraw, blankdata, blankcsv, generic, openvibe, ovdelay:NNN,
  ovsamples:NNN, integer, baseline, path, filter, allmode, eegmode, gyromode,
  noweb, bluetooth, bluetooth=XXXXXXXX
""".strip()


@dataclass
class RunConfig:
    host: str
    port: int
    model: int
    parameters: str = ""


def mirror(custom_string: object) -> None:
    try:
        print(str(custom_string))
    except OSError:
        return


def _normalize_parameters(parameters: str) -> str:
    return str(parameters or "").strip().lower()


def _token_set(parameters: str) -> set[str]:
    return {token for token in _normalize_parameters(parameters).split("+") if token}


def _extract_prefixed_value(parameters: str, prefix: str) -> str | None:
    for token in _token_set(parameters):
        if token.startswith(prefix):
            return token[len(prefix) :]
    return None


def parse_legacy_config(parameters: str) -> tuple[ConnectionOptions, StreamOptions, OutputOptions]:
    normalized = _normalize_parameters(parameters)
    tokens = _token_set(normalized)
    bluetooth_key = _extract_prefixed_value(normalized, "bluetooth=")
    format_value = _extract_prefixed_value(normalized, "format-")
    ovdelay_value = _extract_prefixed_value(normalized, "ovdelay:")
    ovsamples_value = _extract_prefixed_value(normalized, "ovsamples:")

    stream = StreamOptions(
        data_mode=(2 if "gyromode" in tokens else 0 if "allmode" in tokens else 1),
        include_header="noheader" not in tokens,
        baseline="baseline" in tokens,
        filter_enabled="filter" in tokens,
        openvibe="openvibe" in tokens,
        openvibe_delay=int(ovdelay_value) if ovdelay_value and ovdelay_value.isdigit() else 100,
        openvibe_samples=int(ovsamples_value)
        if ovsamples_value and ovsamples_value.isdigit()
        else 4,
    )
    output = OutputOptions(
        format=int(format_value) if format_value and format_value.isdigit() else 0,
        integer_values="integer" in tokens,
        no_counter="nocounter" in tokens,
        no_battery="nobattery" in tokens,
        blank_data="blankdata" in tokens,
        blank_csv="blankcsv" in tokens,
        verbose="verbose" in tokens or "info" in tokens,
        output_data="outputdata" in tokens,
        output_raw="outputraw" in tokens,
    )
    connection = ConnectionOptions(
        transport=Transport.BLUETOOTH if "bluetooth" in normalized else Transport.USB,
        device_key=bluetooth_key,
        confirm_device="confirm" in tokens,
    )
    return connection, stream, output


def _build_client(model: int, parameters: str) -> CyKitClient:
    connection, stream, output = parse_legacy_config(parameters)
    return CyKitClient(Model(model), connection=connection, stream=stream, output=output)


def _info_is_true(io: object | None, name: str) -> bool:
    if io is None:
        return False
    value = io.getInfo(name)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def _active_thread_count(noweb: bool) -> int:
    names = {thread.name for thread in threading.enumerate()}
    count = 0
    if "ioThread" in names:
        count += 1
    if "eegThread" in names:
        count += 1
    return count


def _run_once(config: RunConfig) -> bool:
    parameters = _normalize_parameters(config.parameters)
    noweb = "noweb" in parameters

    client = _build_client(config.model, parameters)
    client.connect()

    if "bluetooth" in parameters:
        mirror("> [Bluetooth] Pairing Device . . .")
    elif not noweb:
        mirror("> Listening on " + config.host + " : " + str(config.port))

    mirror("> Trying Key Model #: " + str(config.model))

    io_thread = None
    try:
        if not noweb:
            io_thread = websocket.socketIO(config.port, 0 if "generic" in parameters else 1, client)
            client.attach_server(io_thread)
            time.sleep(1)
            io_thread.Connect()
            io_thread.start()

        client.start_background_stream()

        if _info_is_true(client.io, "openvibe"):
            time.sleep(3)

        cycle = 3
        while cycle > 2:
            cycle += 1
            time.sleep(0.001)
            if (cycle % 10) != 0:
                continue

            check_threads = 0
            names = {thread.name for thread in threading.enumerate()}
            if "ioThread" in names:
                check_threads += 1
            if "eegThread" in names:
                check_threads += 1

            if _info_is_true(client.io, "openvibe"):
                if check_threads == 0 and io_thread is not None:
                    io_thread.onClose("CyKIT._run() 2")
                    mirror("\r\n*** Reseting . . .")
                    return True
                continue

            if noweb and not _info_is_true(client.io, "stream_ready") and check_threads >= 1:
                continue

            if check_threads < (1 if noweb else 2):
                if io_thread is not None:
                    io_thread.onClose("CyKIT._run() 1")
                mirror("*** Reseting . . .")
                return True
    finally:
        client.close()

    return False


def run_session(config: RunConfig) -> int:
    while True:
        try:
            should_restart = _run_once(config)
        except OSError:
            should_restart = True
        except ConnectionError as exc:
            exc_type, ex, tb = sys.exc_info()
            imported_tb_info = traceback.extract_tb(tb)[-1]
            line_number = imported_tb_info[1]
            print_format = "{}: Exception in line: {}, message: {}"
            mirror("Error in file: " + str(tb.tb_frame.f_code.co_filename) + " >>> ")
            mirror("CyKITv2._run() : " + print_format.format(exc_type.__name__, line_number, ex))
            mirror(traceback.format_exc())
            mirror(" ) WARNING_) CyKIT2._run E1: " + str(exc))
            mirror("Error # " + str(exc))
            return 1
        except Exception as exc:
            exc_type, ex, tb = sys.exc_info()
            imported_tb_info = traceback.extract_tb(tb)[-1]
            line_number = imported_tb_info[1]
            print_format = "{}: Exception in line: {}, message: {}"
            mirror("Error in file: " + str(tb.tb_frame.f_code.co_filename) + " >>> ")
            mirror("CyKITv2._run() : " + print_format.format(exc_type.__name__, line_number, ex))
            mirror(traceback.format_exc())
            mirror(" ) WARNING_) CyKIT2._run E1: " + str(exc))
            mirror("Error # " + str(exc))
            return 1

        if not should_restart:
            return 0


def _validate_model(model: int) -> int:
    if model < 1 or model > 9:
        raise typer.BadParameter("Model must be a numeric value from 1 to 9.")
    return model


def _validate_port(port: int) -> int:
    if port < 1025 or port > 65535:
        raise typer.BadParameter("Port must be in range 1025-65535.")
    return port


def _build_modern_parameters(
    config: str,
    *,
    verbose: bool,
    info: bool,
    confirm: bool,
    noheader: bool,
    nocounter: bool,
    nobattery: bool,
    blankdata: bool,
    blankcsv: bool,
    outputdata: bool,
    outputraw: bool,
    generic: bool,
    openvibe: bool,
    integer: bool,
    baseline: bool,
    filter_enabled: bool,
    allmode: bool,
    gyromode: bool,
    noweb: bool,
    bluetooth_key: str | None,
    bluetooth_auto: bool,
    format_value: int | None,
    ovdelay: int | None,
    ovsamples: int | None,
) -> str:
    tokens = list(_token_set(config))

    def add(token: str, enabled: bool) -> None:
        if enabled and token not in tokens:
            tokens.append(token)

    add("verbose", verbose)
    add("info", info)
    add("confirm", confirm)
    add("noheader", noheader)
    add("nocounter", nocounter)
    add("nobattery", nobattery)
    add("blankdata", blankdata)
    add("blankcsv", blankcsv)
    add("outputdata", outputdata)
    add("outputraw", outputraw)
    add("generic", generic)
    add("openvibe", openvibe)
    add("integer", integer)
    add("baseline", baseline)
    add("filter", filter_enabled)
    add("allmode", allmode)
    add("gyromode", gyromode)
    add("noweb", noweb)

    if bluetooth_key:
        tokens = [
            token for token in tokens if token != "bluetooth" and not token.startswith("bluetooth=")
        ]
        tokens.append(f"bluetooth={bluetooth_key}")
    elif bluetooth_auto and not any(token.startswith("bluetooth") for token in tokens):
        tokens.append("bluetooth")

    if format_value is not None:
        tokens = [token for token in tokens if not token.startswith("format-")]
        tokens.append(f"format-{format_value}")

    if ovdelay is not None:
        tokens = [token for token in tokens if not token.startswith("ovdelay:")]
        tokens.append(f"ovdelay:{ovdelay:03d}")

    if ovsamples is not None:
        tokens = [token for token in tokens if not token.startswith("ovsamples:")]
        tokens.append(f"ovsamples:{ovsamples:03d}")

    if "eegmode" not in tokens and not allmode and not gyromode:
        tokens.append("eegmode")
    if not any(token.startswith("format-") for token in tokens):
        tokens.append("format-0")

    return "+".join(tokens)


def _serialize_device_info(device: DeviceInfo) -> dict[str, object]:
    return {
        "name": device.name,
        "transport": device.transport.value,
        "model_guess": device.model_guess.name if device.model_guess is not None else None,
        "device_key": device.device_key,
        "serial": device.serial,
        "address": device.address,
        "rssi": device.rssi,
        "metadata": dict(device.metadata),
    }


def _print_device_info(device: DeviceInfo) -> None:
    payload = _serialize_device_info(device)
    typer.echo(f"name={payload['name']}")
    typer.echo(f"  transport={payload['transport']}")
    typer.echo(f"  model_guess={payload['model_guess']}")
    typer.echo(f"  device_key={payload['device_key']}")
    typer.echo(f"  serial={payload['serial']}")
    typer.echo(f"  address={payload['address']}")
    typer.echo(f"  rssi={payload['rssi']}")
    typer.echo(f"  metadata={json.dumps(payload['metadata'], ensure_ascii=False, sort_keys=True)}")


@app.command()
def discover(
    transport: Annotated[
        Transport, typer.Option("--transport", help="Transport to scan.")
    ] = Transport.AUTO,
    timeout: Annotated[
        float, typer.Option("--timeout", min=0.1, help="Scan timeout in seconds.")
    ] = 15.0,
    json_output: Annotated[
        bool, typer.Option("--json", help="Print discovery results as JSON.")
    ] = False,
) -> None:
    devices = discover_devices(
        transport=transport, timeout=timeout, probe_gatt=True, probe_timeout=2.0
    )
    if json_output:
        typer.echo(
            json.dumps(
                [_serialize_device_info(device) for device in devices],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return
    if not devices:
        typer.echo("No devices found.")
        return
    for index, device in enumerate(devices, start=1):
        typer.echo(f"[{index}]")
        _print_device_info(device)


def _looks_like_legacy_args(argv: list[str]) -> bool:
    if not argv:
        return False
    first = argv[0]
    if first in {"run", "discover", "help", "--help", "-h", "/?"}:
        return False
    return not first.startswith("-")


def _legacy_config_from_argv(argv: list[str]) -> RunConfig:
    if len(argv) == 1:
        return RunConfig(argv[0], 54123, 1, "")
    if len(argv) == 2:
        return RunConfig(argv[0], int(argv[1]), 1, "")
    if len(argv) == 3:
        return RunConfig(argv[0], int(argv[1]), int(argv[2]), "")
    if len(argv) == 4:
        return RunConfig(argv[0], int(argv[1]), int(argv[2]), argv[3])
    raise typer.BadParameter("Legacy usage accepts at most 4 arguments.")


@app.command()
def run(
    host: str,
    port: int,
    model: Annotated[
        int,
        typer.Argument(
            help="Model number: 1=Epoc Premium, 2=Epoc Consumer, 3=Insight Premium, 4=Insight Consumer, 5=Epoc+ Premium, 6=Epoc+ Consumer 16-bit, 7=Epoc+ Consumer 14-bit"
        ),
    ],
    config: Annotated[str, typer.Argument(help="Legacy + separated config string.")] = "",
    verbose: Annotated[bool, typer.Option("--verbose", help="Enable verbose output.")] = False,
    info: Annotated[
        bool, typer.Option("--info", help="Keep legacy info token for compatibility.")
    ] = False,
    confirm: Annotated[bool, typer.Option("--confirm", help="Confirm device selection.")] = False,
    noheader: Annotated[bool, typer.Option("--noheader", help="Disable CyKITv2 headers.")] = False,
    nocounter: Annotated[bool, typer.Option("--nocounter", help="Drop counter columns.")] = False,
    nobattery: Annotated[bool, typer.Option("--nobattery", help="Drop battery values.")] = False,
    blankdata: Annotated[bool, typer.Option("--blankdata", help="Inject blank data.")] = False,
    blankcsv: Annotated[bool, typer.Option("--blankcsv", help="Add blank CSV columns.")] = False,
    outputdata: Annotated[bool, typer.Option("--outputdata", help="Print decoded output.")] = False,
    outputraw: Annotated[
        bool, typer.Option("--outputraw", help="Print encrypted packets.")
    ] = False,
    generic: Annotated[bool, typer.Option("--generic", help="Use generic TCP mode.")] = False,
    openvibe: Annotated[bool, typer.Option("--openvibe", help="Use OpenViBE mode.")] = False,
    integer: Annotated[bool, typer.Option("--integer", help="Emit integer values.")] = False,
    baseline: Annotated[bool, typer.Option("--baseline", help="Enable baseline mode.")] = False,
    filter_enabled: Annotated[
        bool, typer.Option("--filter", help="Enable baseline filter.")
    ] = False,
    allmode: Annotated[bool, typer.Option("--allmode", help="Emit EEG and gyro packets.")] = False,
    gyromode: Annotated[bool, typer.Option("--gyromode", help="Emit gyro packets only.")] = False,
    noweb: Annotated[
        bool, typer.Option("--noweb", help="Run without TCP/WebSocket listener.")
    ] = False,
    bluetooth_key: Annotated[
        str | None, typer.Option("--bluetooth-key", help="Use a paired Bluetooth device key.")
    ] = None,
    bluetooth_auto: Annotated[
        bool, typer.Option("--bluetooth", help="Auto-detect paired Bluetooth device.")
    ] = False,
    format_value: Annotated[
        int | None, typer.Option("--format", min=0, max=3, help="Output format.")
    ] = None,
    ovdelay: Annotated[
        int | None, typer.Option("--ovdelay", min=0, max=999, help="OpenViBE delay multiplier.")
    ] = None,
    ovsamples: Annotated[
        int | None, typer.Option("--ovsamples", min=1, max=999, help="OpenViBE sample rate.")
    ] = None,
) -> int:
    config_obj = RunConfig(
        host=host,
        port=_validate_port(port),
        model=_validate_model(model),
        parameters=_build_modern_parameters(
            config,
            verbose=verbose,
            info=info,
            confirm=confirm,
            noheader=noheader,
            nocounter=nocounter,
            nobattery=nobattery,
            blankdata=blankdata,
            blankcsv=blankcsv,
            outputdata=outputdata,
            outputraw=outputraw,
            generic=generic,
            openvibe=openvibe,
            integer=integer,
            baseline=baseline,
            filter_enabled=filter_enabled,
            allmode=allmode,
            gyromode=gyromode,
            noweb=noweb,
            bluetooth_key=bluetooth_key,
            bluetooth_auto=bluetooth_auto,
            format_value=format_value,
            ovdelay=ovdelay,
            ovsamples=ovsamples,
        ),
    )
    return run_session(config_obj)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if ctx.args:
        legacy = _legacy_config_from_argv(ctx.args)
        legacy.port = _validate_port(legacy.port)
        legacy.model = _validate_model(legacy.model)
        raise typer.Exit(run_session(legacy))
    typer.echo(HELP_TEXT)
    raise typer.Exit()


def cli(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if _looks_like_legacy_args(arguments):
        legacy = _legacy_config_from_argv(arguments)
        legacy.port = _validate_port(legacy.port)
        legacy.model = _validate_model(legacy.model)
        return run_session(legacy)
    try:
        return int(app(args=arguments, prog_name="cykit", standalone_mode=False) or 0)
    except typer.Exit as exc:
        return int(exc.exit_code or 0)
    except typer.BadParameter as exc:
        typer.echo(str(exc), err=True)
        return 2
    except Exception as exc:
        typer.echo(str(exc), err=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
