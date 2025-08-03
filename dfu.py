import usb.core
import usb.util

STM_VENDOR_ID: int = 0x0483
FLASH_START: int = 0x08000000


def find_dfu_devices() -> list[usb.Device]:
    found = usb.core.find(idVendor=STM_VENDOR_ID, find_all=True)
    return [] if found is None else list(found)


def get_transfer_size(dev: usb.Device) -> int:
    for cfg in dev.configurations():
        for intf in cfg.interfaces():
            if len(intf.extra_descriptors) != 0 and intf.extra_descriptors[1] == 0x21:
                return intf.extra_descriptors[6] << 8 + intf.extra_descriptors[5]


def get_status(dev: usb.Device) -> tuple[int, str]:
    data = dev.ctrl_transfer(
        bmRequestType=0b10100001,
        bRequest=3,
        wValue=0,
        wIndex=0,
        data_or_wLength=6,
    )
    return data


def download(dev: usb.Device, block_num: int, data: bytes, should_ignore: bool = False):
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
    dev.ctrl_transfer(
        bmRequestType=0b00100001,
        bRequest=0,
        wValue=1000,
        wIndex=0,
        data_or_wLength=None,
    )
