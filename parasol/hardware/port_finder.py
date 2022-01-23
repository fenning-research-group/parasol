import serial.tools.list_ports as lp


def get_port(device_identifiers):
    """Finds port address for given device identifiers

    Returns:
        str: port address
    """

    port = _get_port_windows(device_identifiers)

    if port is None:
        raise ValueError(f"Device not found!")
    return port


def _get_port_windows(device_identifiers):
    for p in lp.comports():
        match = True
        for attr, value in device_identifiers.items():
            if getattr(p, attr) != value:
                match = False
        if match:
            return p.device
    raise ValueError("Cannot find a matching port!")
