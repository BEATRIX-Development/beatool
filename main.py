import pyfiglet
import tqdm
import colorama
import textwrap
import dfu
import usb.core
import time
import usb.util
import usb
import usb.control
import math

TITLE_FONT = pyfiglet.Figlet(font="slant")
SCREEN_WIDTH = 80
OPENING_MESSAGE = """
Welcome to BeaTool, which you can use to access, configure, and flash Flipper Zeroes with the BEATRIX firmware!
""".strip()
BANNER = TITLE_FONT.renderText("BeaTool")
BANNER_COLORS = [
    colorama.Fore.RED,
    colorama.Fore.LIGHTRED_EX,
    colorama.Fore.WHITE,
    colorama.Fore.LIGHTBLUE_EX,
    colorama.Fore.BLUE,
]


def print_banner():
    for color, line in zip(BANNER_COLORS, BANNER.splitlines()):
        print(colorama.Style.BRIGHT + color + line)
    print(colorama.Style.RESET_ALL)


def output_text(text: str, /, bold: bool = True):
    if bold:
        print(colorama.Style.BRIGHT, end="")
    print("\n".join(textwrap.wrap(text, replace_whitespace=False, width=SCREEN_WIDTH)))
    print(colorama.Style.RESET_ALL)


def scan_devices() -> tuple[list[usb.core.Device], dict[str, str]]:
    dev_list = dfu.find_dfu_devices()
    device_str = f"Found {len(dev_list)} device{'s' if len(dev_list) != 1 else ''}."
    options = {
        "R": "Re-scan",
        "Q": "Quit",
    }
    if len(dev_list) == 0:
        device_str += (
            " Are you sure you've connected your Flipper and that it's in DFU mode?"
        )
    else:
        options |= {
            "F": "Flash all devices",
            "C": "Choose a single device to flash",
        }
    output_text(device_str)
    return (dev_list, options)


def download_file(filename: str, dev: usb.Device):
    with open(filename, "rb") as f:
        data = f.read()
    n_blocks = math.ceil(len(data) / dfu.get_transfer_size(dev))
    dev.ctrl_transfer(
        bmRequestType=0b00100001,
        bRequest=1,
        wValue=0,
        wIndex=0,
        data_or_wLength=bytes([0x21, 0x00, 0x00, 0x00, 0x08]),
    )
    is_working = True
    while is_working:
        try:
            is_working = dfu.get_status(dev)[4] not in [2, 5]
        except Exception as e:
            print(e)
    for i in tqdm.tqdm(range(n_blocks), ncols=SCREEN_WIDTH):
        dfu.download(dev, i + 2, data[i * 1024 : (i + 1) * 1024])
    dfu.download(dev, 0, b"", should_ignore=True)
    try:
        # This will fail. We don't care. We need to do it anyway.
        dfu.get_status(dev)
    except:
        pass


def main():
    colorama.init()
    print_banner()
    output_text(OPENING_MESSAGE)
    output_text("Let's get started by scanning for DFU devices:")
    time.sleep(0.5)
    devices, options = scan_devices()
    time.sleep(0.5)
    output_text("What would you like to do?")
    output_text("\n".join([f"({opt}) {options[opt]}" for opt in options.keys()]))
    while True:
        choice = input(colorama.Style.BRIGHT + "> " + colorama.Style.RESET_ALL)
        while choice not in options.keys():
            output_text(colorama.Fore.RED + "Invalid choice. Please choose again.")
            choice = input(colorama.Style.BRIGHT + "> " + colorama.Style.RESET_ALL)
        print()
        match choice:
            case "R":
                output_text("Re-scanning...")
                time.sleep(0.5)
                devices, options = scan_devices()
                time.sleep(0.5)
                output_text("What would you like to do now?")
                do_choose = True
                continue
            case "Q":
                output_text("Quitting BeaTool.")
                exit(0)
            case "F":
                for dev in devices:
                    output_text(
                        f"Now flashing device with serial number {usb.util.get_string(dev, dev.iSerialNumber)}"
                    )
                    download_file(
                        "/home/juniper/Documents/beatrix/bin/release.bin", dev
                    )
        break


if __name__ == "__main__":
    main()
