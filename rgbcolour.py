#!/usr/bin/env python3

# manipulate box colours

def read_colour_file():
    """Return a dictionary mapping colour names to RGB channels in range 0..1."""
    with open("/etc/X11/rgb.txt") as instream:
        return {
            splitline[1].strip(): [float(elt)/255.0
                                   for elt in splitline[0].split()]
            for splitline in [line.split("\t\t")
                              for line in instream.readlines()[1:]]}

COLOUR_TABLE = None

def rgbcolour(name: str, opacity:float = 1.0):
    global COLOUR_TABLE
    if not COLOUR_TABLE:
        COLOUR_TABLE = read_colour_file()
    return COLOUR_TABLE[name] + [opacity]

# for testing:
if __name__ == "__main__":
    for name, value in read_colour_file().items():
        print(name, "is", value)
