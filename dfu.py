import usb.core
import usb.util

STM_VENDOR_ID: int = 0x0483


def find_dfu_devices() -> list[usb.Device]:
    """
    Find attached STM32 devices in DFU mode

    Returns: list of attached STM32 devices in usb.Device format
    """
    found = usb.core.find(idVendor=STM_VENDOR_ID, find_all=True)
    return [] if found is None else list(found)


def get_transfer_size(dev: usb.Device) -> int:
    """
    Get the DFU transfer size of an attached device

    Takes: the device as a usb.Device
    Returns: the DFU transfer size in bytes
    """
    for cfg in dev.configurations():
        for intf in cfg.interfaces():
            if len(intf.extra_descriptors) != 0 and intf.extra_descriptors[1] == 0x21:
                return intf.extra_descriptors[6] << 8 + intf.extra_descriptors[5]


def get_status(dev: usb.Device) -> list[int]:
    """
    Get the status of an attached DFU device

    Takes: the device as a usb.Device
    Returns: the status as specified in the DFU standard (as a list of ints, which can
    be converted to a bytearray or bytes object if needed)
    """
    data = dev.ctrl_transfer(
        bmRequestType=0b10100001,
        bRequest=3,
        wValue=0,
        wIndex=0,
        data_or_wLength=6,
    )
    return data


def download(dev: usb.Device, block_num: int, data: bytes, should_ignore: bool = False):
    """
    Download data to a DFU device

    Takes: the device as a usb.Device, the block number to start writing from, the data
    to write in byte format, and optionally a bool indicating whether or not the function
    should ignore the status of the device after transfer and return immediately
    """
    dev.ctrl_transfer(
        bmRequestType=0b00100001,
        bRequest=1,
        wValue=block_num,
        wIndex=0,
        data_or_wLength=data,
    )
    if should_ignore:
        return
    is_working = True
    while is_working:
        try:
            is_working = get_status(dev)[4] not in [2, 5]
        except Exception as e:
            print(e)


def detach(dev: usb.Device):
    """
    Issue a DETACH command to an attached DFU device

    Takes: the device as a usb.Device
    """
    dev.ctrl_transfer(
        bmRequestType=0b00100001,
        bRequest=0,
        wValue=1000,
        wIndex=0,
        data_or_wLength=None,
    )
