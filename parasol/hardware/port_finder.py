import serial.tools.list_ports as lp


def get_port(device_identifiers):
    """Finds port address for given device identifiers

    Returns:
        str: port address
    """

    # Get port on windows
    port = _get_port_windows(device_identifiers)

    # Raise error if we can't find it, else return port
    if port is None:
        raise ValueError(f"Device not found!")
    return port


def _get_port_windows(device_identifiers):
    """Finds port address for given device identifiers on Windows"""

    # Cycle throgh ports, if all atrributes match for anything then return port, else error
    for p in lp.comports():
        match = True
        for attr, value in device_identifiers.items():
            if int(getattr(p, attr)) != int(value):
                match = False
        if match:
            return p.device
    raise ValueError("Cannot find a matching port!")
