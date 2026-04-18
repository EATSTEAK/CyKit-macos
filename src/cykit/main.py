# -*- coding: utf8 -*-
#
#  CyKIT   2021.Nov.10
# ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
#  main.py (formerly CyKIT.py)
#  Written by Warren
#
#  Launcher to initiate EEG setup.
#  ¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯

import os
import sys
import threading
import time
import traceback

from cykit.client import CyKitClient
from cykit.models import ConnectionOptions, Model, OutputOptions, StreamOptions, Transport
from cykit import websocket


def mirror(custom_string):
        try:
            print(str(custom_string))
            return
        except OSError as exp:
            return


def _build_client(model: int, parameters: str) -> CyKitClient:
    transport = Transport.BLUETOOTH if "bluetooth" in parameters else Transport.USB
    device_key = None
    if "bluetooth=" in parameters:
        split_bt = parameters.split("bluetooth=")
        if len(split_bt) > 1:
            device_key = split_bt[1].split("+")[0]

    stream = StreamOptions(
        data_mode=(2 if "gyromode" in parameters else 0 if "allmode" in parameters else 1),
        include_header="noheader" not in parameters,
        baseline="baseline" in parameters,
        filter_enabled="filter" in parameters,
        openvibe="openvibe" in parameters,
    )
    output = OutputOptions(
        format=int(parameters.split("format-")[1][:1]) if "format-" in parameters else 0,
        integer_values="integer" in parameters,
        no_counter="nocounter" in parameters,
        no_battery="nobattery" in parameters,
        blank_data="blankdata" in parameters,
        blank_csv="blankcsv" in parameters,
        verbose="verbose" in parameters,
        output_data="outputdata" in parameters,
        output_raw="outputraw" in parameters,
    )
    connection = ConnectionOptions(
        transport=transport,
        device_key=device_key,
        confirm_device="confirm" in parameters,
    )
    return CyKitClient(Model(model), connection=connection, stream=stream, output=output)


def _run(CyINIT):
    HOST = str(sys.argv[1])
    PORT = int(sys.argv[2])
    MODEL = int(sys.argv[3])
    parameters = str(sys.argv[4]).lower()
    noweb = "noweb" in parameters

    client = _build_client(MODEL, parameters)
    client.connect()

    if "bluetooth" in parameters:
        mirror("> [Bluetooth] Pairing Device . . .")
    elif not noweb:
        mirror("> Listening on " + HOST + " : " + str(PORT))

    mirror("> Trying Key Model #: " + str(MODEL))

    ioTHREAD = None
    if not noweb:
        ioTHREAD = websocket.socketIO(PORT, 0 if "generic" in parameters else 1, client)
        client.attach_server(ioTHREAD)
        time.sleep(1)
        ioTHREAD.Connect()
        ioTHREAD.start()

    client.start_background_stream()

    if client.io is not None and eval(client.io.getInfo("openvibe")) == True:
        time.sleep(3)

    CyINIT = 3
    while CyINIT > 2:
        CyINIT += 1
        time.sleep(.001)

        if (CyINIT % 10) != 0:
            continue

        check_threads = 0
        t_array = str(list(map(lambda x: x.name, threading.enumerate())))
        if 'ioThread' in t_array:
            check_threads += 1
        if 'eegThread' in t_array:
            check_threads += 1

        if client.io is not None and eval(client.io.getInfo("openvibe")) == True:
            if check_threads == 0 and ioTHREAD is not None:
                ioTHREAD.onClose("CyKIT._run() 2")
                mirror("\r\n*** Reseting . . .")
                client.close()
                CyINIT = 1
                _run(1)
            continue

        if check_threads < (1 if noweb else 2):
            if ioTHREAD is not None:
                ioTHREAD.onClose("CyKIT._run() 1")
            mirror("*** Reseting . . .")
            client.close()
            CyINIT = 1
            _run(1)


def cli():
    """Entry point for ``python -m cykit`` and the ``cykit`` console script."""

    arg_count = len(sys.argv)

    if arg_count == 1 or arg_count > 5 or sys.argv[1] == "help" or sys.argv[1] == "--help" or sys.argv[1] == "/?":
        mirror("\r\n")
        mirror(" (Version: CyKIT 4.0) for Python 3.x on (Windows / macOS / Linux) \r\n")
        mirror("\r\n Usage:  cykit <IP> <Port> <Model#(1-7)> [config] \r\n\r\n")
        mirror(" " + "═" * 100 + "\r\n")
        mirror(" <IP> <PORT> for CyKIT to listen on. \r\n")
        mirror(" " + ("═" * 100) + "\r\n")
        mirror(" <Model#> Choose the decryption type. \r\n")
        mirror("          1 - Epoc    (Premium  Model)\r\n")
        mirror("          2 - Epoc    (Consumer Model)\r\n")
        mirror("          3 - Insight (Premium  Model)\r\n")
        mirror("          4 - Insight (Consumer Model) \r\n")
        mirror("          5 - Epoc+   (Premium  Model)\r\n")
        mirror("          6 - Epoc+   (Consumer Model) [16-bit EPOC+ mode] \r\n\r\n")
        mirror("          7 - EPOC+   (Consumer Model) [14-bit EPOC  mode] \r\n")
        mirror(" " + "═" * 100 + "\r\n")
        mirror(" [config] is optional. \r\n")
        mirror("  'info'                Prints additional information into console.\r\n\r\n")
        mirror("  'confirm'             Requests you to confirm a device everytime device is initialized.\r\n\r\n")
        mirror("  'verbose'             Prints extra information regarding the inner workings of CyKIT.\r\n\r\n")
        mirror("  'nocounter'           Removes COUNTER and INTERPOLATE from outputs. (Must also use either nogyro or noeeg) \r\n")
        mirror("                         (nogyro is enabled by default.) This ensures streams are differentiated. \r\n\r\n")
        mirror("  'noheader'            Removes CyKITv2::: header information. (Required for openvibe) \r\n\r\n")
        mirror("  'format-0'            (Default) Outputs 14 data channels in float format. ('4201.02564096') \r\n\r\n")
        mirror("  'format-1'            Outputs the raw data (to be converted by Javascript or other). \r\n\r\n")
        mirror("  'format-3'            Used only with Insight(USB), selects specific bit ranges to acquire data.\r\n\r\n")
        mirror("  'outputdata'          Prints the (formatted) data being sent, to the console window.\r\n\r\n")
        mirror("  'outputraw'           Prints the (encrypted) rjindael data to the console window.\r\n\r\n")
        mirror("  'blankdata'           Injects a single line of encrypted data into the stream that is \r\n")
        mirror("                         consistent with a blank EEG signal. Counter will report 0. \r\n\r\n")
        mirror("  'blancsv'             Adds blank channels for each CSV line, to be used with logging.\r\n\r\n")
        mirror("  'generic'             Connects to any generic program via TCP. (Can be used with other flags.)\r\n\r\n")
        mirror("  'openvibe'            Connects to the generic OpenViBE Acquisition Server.\r\n\r\n")
        mirror("                         must use generic+nocounter+noheader+nobattery Other flags are optional.\r\n")
        mirror("  'ovdelay'             Stream sending delay. (999 maximum) Works as a multiplier, in the format: ovdelay:001 \r\n\r\n")
        mirror("  'ovsamples'           Changes openvibe sample rate. Format: ovsamples:001 \r\n\r\n")
        mirror("  'integer'             Changes format from float to integer. Works with other flags. Including openvibe. \r\n\r\n")
        mirror("  'baseline'            Averages data and sends the baseline value to socket.\r\n\r\n")
        mirror("  'path'                Prints the Python paths used to acquire modules.\r\n\r\n")
        mirror("  'filter'              When used with baseline, subtracts the data value from baseline and sends to sockets.\r\n\r\n")
        mirror("  'allmode'             Sends Gyro and EEG data packets (Can change during run-time)\r\n\r\n")
        mirror("  'eegmode'             Sends only EEG packets. (Can change during run-time)\r\n\r\n")
        mirror("  'gyromode'            Sends only Gyro packet. (Can change during run-time)\r\n\r\n")
        mirror("  'noweb'               Displays data. (without requiring a TCP connection.)\r\n\r\n")
        mirror("  'bluetooth'  Attempt to AUTO-DETECT an already paired bluetooth device.\r\n\r\n")
        mirror("  'bluetooth=xxxxxxxx'  Connect to an already paired bluetooth device, use the hex digit found in the devices pairing name.\r\n\r\n")
        mirror("                         The pairing name can be found in OS Bluetooth settings.\r\n\r\n")
        mirror("   Join these options (in any order), using a + separator. \r\n")
        mirror("   (e.g  info+confirm ) \r\n\r\n")
        mirror(" " + "═" * 100 + "\r\n")
        mirror("  Example Usage: \r\n")
        mirror("  cykit 127.0.0.1 54123 1 info+confirm \r\n\r\n")
        mirror("  Example Usage: \r\n")
        mirror("  cykit 127.0.0.1 5555 6 openvibe+generic+nocounter+noheader+nobattery+ovdelay:100+integer+ovsamples:004 \r\n\r\n")
        mirror(" " + "═" * 100 + "\r\n")
        sys.argv = [sys.argv[0], "127.0.0.1", "54123", "1", ""]


    if arg_count < 5:

        if arg_count == 2:
            sys.argv = [sys.argv[0], sys.argv[1], "54123", "1", ""]
        if arg_count == 3:
            sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], "1", ""]
        if arg_count == 4:
            sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], sys.argv[3], ""]

    if sys.argv[2].isdigit() == False or int(sys.argv[2]) < 1025 or int(sys.argv[2])> 65535:
        mirror("Invalid Port #[" + str(sys.argv[2]) + "] (Must be a local port in range: 1025 - 65535)")
        os._exit(0)

    if sys.argv[3].isdigit() == False:
        mirror("Invalid Key # [" + str(sys.argv[3]) + "] (Must be a numeric 1 - 9)")
        os._exit(0)

    if int(sys.argv[3]) < 1 or int(sys.argv[3]) > 9:
        mirror("Invalid Key # [" + str(sys.argv[2]) + "] (Must be a numeric 1-9)")
        os._exit(0)

    try:
        try:
            _run(1)
        except OSError as exp:
            _run(1)

    except Exception as e:
        exc_type, ex, tb = sys.exc_info()
        imported_tb_info = traceback.extract_tb(tb)[-1]
        line_number = imported_tb_info[1]
        print_format = '{}: Exception in line: {}, message: {}'

        mirror("Error in file: " + str(tb.tb_frame.f_code.co_filename) + " >>> ")
        mirror("CyKITv2._run() : " + print_format.format(exc_type.__name__, line_number, ex))
        mirror(traceback.format_exc())

        mirror(" ) WARNING_) CyKIT2._run E1: " + str(e))
        mirror("Error # " + str(e))
        mirror("> Device Time Out or Disconnect . . .  [ Reconnect to Server. ]")
        _run(1)


if __name__ == "__main__":
    cli()
