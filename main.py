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
import os
import urllib3
import yaspin

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
# In form "Release Name": "https://release.url/file.bin"
KNOWN_RELEASES: dict[str, str] = {}
HTTP = urllib3.PoolManager(timeout=10)


def print_banner():
    """
    Prints the BeaTool banner.
    """
    for color, line in zip(BANNER_COLORS, BANNER.splitlines()):
        print(colorama.Style.BRIGHT + color + line)
    print(colorama.Style.RESET_ALL)


def output_text(text: str, /, bold: bool = True):
    """
    Prints out text after wrapping it and styling it as necessary

    Takes: the text as a string, and optionally a boolean indicating if text should be
    bolded
    """
    if bold:
        print(colorama.Style.BRIGHT, end="")
    print("\n".join(textwrap.wrap(text, replace_whitespace=False, width=SCREEN_WIDTH)))
    print(colorama.Style.RESET_ALL)


def scan_devices() -> tuple[list[usb.core.Device], dict[str, str]]:
    """
    Manages the UI for scanning for devices.

    Returns: a tuple with a list of devices and a dictionary of available options,
    with option letters being mapped to option titles
    """
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
        }
    output_text(device_str)
    return (dev_list, options)


def download_file(url: str) -> bytes:
    """
    Downloads a file from the Internet with helpful messages and a couple spinners.

    Takes: a string indicating the URL to download from
    Returns: the data in `bytes` form
    """
    try:
        with yaspin.yaspin():
            r = HTTP.request(
                "GET",
                KNOWN_RELEASES[opts[choice]],
                preload_content=False,
            )
    except Exception as e:
        output_text(colorama.Fore.RED + "Failed to open HTTP connection.")
        raise e
    if r.status != 200:
        output_text(
            colorama.Fore.RED + f"Failed to fetch remote file (HTTP status {r.status})."
        )
        exit(-1)
    output_text("Connection created.")
    result = b""
    with yaspin.yaspin():
        while True:
            data = r.read(1024)
            if not data:
                break
            result += data
    r.release_conn()
    output_text("File downloaded.")
    return result


def pick_file_or_release() -> bytes:
    """
    Manages the GUI for picking a file or a known release.

    Returns: the data from the user's choice
    """
    if len(KNOWN_RELEASES) > 0:
        text = "Would you like to flash an existing file or download a known release?"
        text += " Known releases include "
        if len(KNOWN_RELEASES) == 1:
            text += list(KNOWN_RELEASES.keys())[0]
        elif len(KNOWN_RELEASES) == 2:
            text += " and ".join(KNOWN_RELEASES.keys())
        else:
            releases = list(KNOWN_RELEASES.keys())
            text += ", ".join(releases[:-1])
            text += f", and {releases[-1]}"
        text += "."
        output_text(text)

        opts = {
            str(i): s for i, s in enumerate(["Choose a file", *KNOWN_RELEASES.keys()])
        }
        choice_str = "\n".join([f"({i}) {s}" for i, s in opts.items()])
        output_text(choice_str)
        choice = input(colorama.Style.BRIGHT + "> " + colorama.Style.RESET_ALL)
        while choice not in opts.keys():
            output_text(colorama.Fore.RED + "Invalid choice. Please choose again.")
            choice = input(colorama.Style.BRIGHT + "> " + colorama.Style.RESET_ALL)
        print()

        if choice != "0":
            return download_file(KNOWN_RELEASES[opts[choice]])

    output_text("Enter the absolute path of the .bin file.")
    choice = input(colorama.Style.BRIGHT + "> " + colorama.Style.RESET_ALL)
    while not os.path.exists(choice):
        output_text(
            colorama.Fore.RED
            + "Invalid choice (file does not exist). Please choose again."
        )
        choice = input(colorama.Style.BRIGHT + "> " + colorama.Style.RESET_ALL)
    print()

    with open(choice, "rb") as f, yaspin.yaspin():
        result = f.read()
    return result


def download_bin(data: bytes, dev: usb.Device):
    """
    Manages the GUI for flashing binary data onto the device.

    Takes: the data in bytes, and the device as a usb.Device
    """
    n_blocks = math.ceil(len(data) / dfu.get_transfer_size(dev))
    output_text(f"Downloading a total of {n_blocks} blocks (usually KiB).")
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
            output_text(colorama.Fore.RED + "Reading USB status failed.")
            raise e
    for i in tqdm.tqdm(range(n_blocks), ncols=SCREEN_WIDTH, unit="bl"):
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
                data = pick_file_or_release()
                for dev in devices:
                    output_text(
                        f"Now flashing device with serial number {usb.util.get_string(dev, dev.iSerialNumber)}."
                    )
                    download_bin(data, dev)
                    print()
                    output_text("Device flashed.")
        break
    output_text("Now exiting. Have a nice day!")


if __name__ == "__main__":
    main()
