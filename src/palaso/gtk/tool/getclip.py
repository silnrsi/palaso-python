#!/usr/bin/env python3
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk, Gdk
import pprint
import sys
from subprocess import Popen, PIPE


def main():
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    text = str(clipboard.wait_for_text())
    if (len(sys.argv) > 1 and sys.argv[1] == "-p") :
        pprint.pprint(text)
    elif (len(sys.argv) > 1 and sys.argv[1] == "-s") :
        for s in text :
            print(f"{ord(s):04X} ", end='')
        print('')
    elif len(sys.argv) > 1 and sys.argv[1] == '-e' :
        p = Popen(sys.argv[2:], stdout=PIPE, stdin=PIPE)
        res = p.communicate(text)
        clipboard.set_text(res[0])
        clipboard.store()
    else :
        print(text)


if __name__ == "__main__":
    main()
