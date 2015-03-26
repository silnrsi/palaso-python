
from xml.etree.ElementTree import XMLTreeBuilder
import os.path

class xmlmodel(object) :
    def __init__(self, parent = None) :
        self.data = {}
        self.axes = {}
        self.parent = parent

    def parse_file(self, fname) :
        if os.path.exist(fname) :
            self.xml = XMLTreeBuilder(target=self)
            self.xml.curr = self
            fh = file(fname)
            self.xml.feed(fh.read())

    def set_key(self, key, value) :
        if len(key) > 1 :
            if not self.axes.has_key(key[0]) :
                self.axes[key[0]] = xmlmodel(self)
            self.axes[key[0]].set_key(key[1:], value)
        else :
            self.data[key[0]] = value

    def get_key(self, key) :
        if len(key) > 1 :
            if not self.axes.has_key(key[0]) :
                return None
            return self.axes[key[0]].get_key(key[1:])
        else :
            return self.data.get(key[0])

    def start(self, name, attrs) :
        if name == "data" :
            self.xml.currkey = attrs['key']
        elif name == 'axis' :
            newaxis = xmlmodel(self.xml.curr)
            self.axes[attrs['key']] = newaxis
            self.xml.curr = newaxis

    def data(self, text) :
        if self.xml.currkey :
            self.xml.curr[self.xml.currkey] = text

    def end(self, name) :
        if name == "axis" and self.xml.curr.parent :
            self.xml.curr = self.xml.curr.parent

    def save(self, fname) :
        fh = file(fname, "w")
        fh.writelines(("<?xml version='1.0'?>\n",
                       "<palaso_model>\n"))
        self.write_xml(fh, "")
        fh.write("</palaso_model>\n")

    def write_xml(self, fh, indent) :
        indent += "  "
        for (k, v) in self.data.iteritems() :
            fh.write("%s<data key='%s'>%s</data>\n" % (indent, k, v))
        for (k, v) in self.axes.iteritems() :
            fh.write("%s<axis key='%s'>\n" % (indent, k))
            v.write_xml(fh, indent)
            fh.write("%s</axis>\n" % (indent))

