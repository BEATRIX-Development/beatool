# BeaTool

Interactive CLI tool for flashing the BEATRIX firmware to Flipper Zeroes.

## Installation

**Due to development limitations, BeaTool currently only supports Linux and is untested on macOS and WSL.**

If you're running NixOS, you're in luck! To drop into a shell where you can run BeaTool immediately without needing to install anything permanently, simply run `nix develop` in the base `beatool` directory. If you don't have flakes enabled systemwide, you might need to add the option ` --experimental-features 'nix-command flakes'` to get it to work.

Otherwise, make sure you have the following things installed:
- `libusb1`
- `uv`

Additionally, to be able to run BeaTool as a regular user, you may need to add the following to your `udev` rules:

```udev
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="df11", ATTRS{manufacturer}=="STMicroelectronics", MODE="0666"
```

If you've already modified your `udev` rules to use qFlipper, this line should **replace** the line in there with the same `idVendor` and `idProduct` values.

## Running

If you have everything installed, you can just run `uv run main.py` in the base directory and everything should work.

## Simple Questions

### It says it doesn't detect my Flipper!

Ensure that it is in **DFU mode** (which can be accessed by unplugging any USB connections and holding down the BACK and center buttons for 30 seconds) and, of course, that it is plugged in to your computer.

### When will this support (X feature)?

Feel free to make a GitHub issue for it! Do keep in mind that BeaTool currently only has one maintainer, and features take time.

## Links
- [Discussion Room for BEATRIX and BeaTool](https://matrix.to/#/#beatrix:gitter.im), run using Gitter/Matrix. You will need either a Matrix or a Github account.

## To-Do
- Add a non-interactive mode
- Add firmware verification and validation