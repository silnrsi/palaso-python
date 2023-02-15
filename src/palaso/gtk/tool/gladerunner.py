#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import sys
from palaso.gtk.actionpack import Simple


class App :
    def __init__(self, glade) :
        self.builder = Gtk.Builder()
        self.builder.add_from_file(glade)
        self.pack = Simple()
        self.builder.connect_signals(self.pack)
        self.window = self.builder.get_object("window1")
        self.window.show()

    def run(self) :
        Gtk.main()


def main():
    app = App(sys.argv[1])
    return app.run()


if __name__ == "__main__":
    main()
