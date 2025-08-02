import pyfiglet

TITLE_FONT = pyfiglet.Figlet(font="slant")


def main():
    print(TITLE_FONT.renderText("BeaTool"))


if __name__ == "__main__":
    main()
