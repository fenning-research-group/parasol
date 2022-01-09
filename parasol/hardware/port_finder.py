import serial.tools.list_ports as lp

def get_port(device_identifiers):
    """ Finds port address for given device identifiers

    Returns:
        str: port address
    """    

    for p in lp.comports():
        match = True
        for attr, value in device_identifiers.items():
            if getattr(p, attr) != value:
                match = False
        if match:
            return p.device
    raise ValueError("Cannot find a matching port!")
