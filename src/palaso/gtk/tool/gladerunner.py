#!/usr/bin/env python3

import pygtk
pygtk.require('2.0')
import gtk, sys
from palaso.gtk.actionpack import Simple


class App :
    def __init__(self, glade) :
        self.builder = gtk.Builder()
        self.builder.add_from_file(glade)
        self.pack = Simple()
        self.builder.connect_signals(self.pack)
        self.window = self.builder.get_object("window1")
        self.window.show()

    def run(self) :
        gtk.main()


def main():
    app = App(sys.argv[1])
    return app.run()


if __name__ == "__main__":
    main()
