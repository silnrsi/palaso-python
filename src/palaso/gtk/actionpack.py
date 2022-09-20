import gtk
from palaso.gtk.templang import lang

class View :

    def __init__(self, gfile) :
        self.builder = gtk.Builder()
        self.builder.add_from_file(gfile)
        self.parse_file(gfile)
        self.properties = {}

    def parse_file(self, model, gfile) :
        tree = ElementTree()
        tree.parse(gfile)
        for e in tree.findall("//object") :
            obj = self.builder.get_object(e.attrib["id"])
            obj.properties={}
            for s in e.findall("signal") :
                if e.attrib["after"] :
                    obj.connect_after(e.attrib["name"], e.attrib["callback"], e.get("object"))
            for p in e.findall("property") :
                if lang.test_expr(p.text) :
                    obj.properties[p.attrib["name"]] = Expr(p.text, p.attrib["name"], model, obj)

class Expr :

    def __init__(self, exprstr, name, model, obj) :
        self.expr = lang(exprstr, model)
        self.obj = obj
        self.name = name
        for f in self.property_map :
            if isinstance(obj, f[0]) and name == f[1]:
                self.setter = f[2]
                break

    def update(self) :
        res = self.expr.calc()
        if self.setter : getattr(self.obj, self.setter)(res)
        elif self.name : self.obj.__setattr__(self.name, res)


class Simple :

    def __init__(self) :
        self.vars={}

    def do_window_destroy(self, widget, data=None) :
        gtk.main_quit()

    def do_popup(self, widget, data=None, data1=None) :
        print(data)
        print(data1)

