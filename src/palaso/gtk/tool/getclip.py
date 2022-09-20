#!/usr/bin/env python3

import gtk
import pprint
import sys
from subprocess import Popen, PIPE


def main():
    clipboard = gtk.clipboard_get()
    text = str(clipboard.wait_for_text())
    if (len(sys.argv) > 1 and sys.argv[1] == "-p") :
        pprint.pprint(text)
    elif (len(sys.argv) > 1 and sys.argv[1] == "-s") :
        for s in text :
            print(f"{ord(s):04X}"),
    elif len(sys.argv) > 1 and sys.argv[1] == '-e' :
        p = Popen(sys.argv[2:], stdout=PIPE, stdin=PIPE)
        res = p.communicate(text)
        clipboard.set_text(res[0])
        clipboard.store()
    else :
        print(text)


if __name__ == "__main__":
    main()
