"""ElementTree parser that gives parser context. Useable in py3"""

from xml.etree.ElementTree import TreeBuilder, Element

class XMLParser:
    def __init__(self, html=0, target=None, encoding=None):
        try: from xml.parser import expat
        except ImportError:
            try: import pyexpat as expat
            except ImportError:
                raise ImportError("No module named expat")
        self.parser = expat.ParserCreate(encoding, "}")
        if target is None:
            target = TreeBuilder()
        self.target = target
        self._error = expat.error
        self._names = {}
        self.entity = {}
        parser = self.parser
        parser.DefaultHandlerExpand = self._default
        for k, v in {"start": (self._start, "StartElementHandler"),
                     "end": (self._end, "EndElementHandler"),
                     "data": (None, "CharacterDataHandler"),
                     "comment": (None, "CommentHandler"),
                     "pi": (None, "ProcessingInstructionHandler")}.items():
            if hasattr(target, k):
                setattr(parser, v[1], v[0] if v[0] is not None else getattr(target, k))
        parser.buffer_text = 1
        parser.ordered_attributes = 1
        parser.specified_attributes = 1
        self.positions = {}

    def _raiseerrror(self, msg, code):
        err = self.error(msg + ": line {:d}, column {:d}")
        err.code = code
        err.lineno = self.parser.ErrorLineNumber
        err.offset = self.parser.ErrorColumnNumber
        raise err

    def _fixname(self, key):
        try:
            return self._names[key]
        except KeyError:
            name = key
            if "}" in name:
                name = "{" + name
            self._names[key] = name
            return name

    def _start(self, tag, attr_list):
        fixname = self._fixname
        tag = fixname(tag)
        attrib = {fixname(k): v for (k, v) in zip(attr_list[::2], attr_list[1::2])}
        res = self.target.start(tag, attrib)
        # This whole module exists to add this one line!
        self.positions[id(res)] = (self.parser.CurrentLineNumber, self.parser.CurrentColumnNumber)
        return res

    def _end(self, tag):
        return self.target.end(self._fixname(tag))

    def _default(self, text):
        prefix = text[:1]
        if prefix == "&":
            try: data_handler = self.target.data
            except AttributeError: return
            try: data_handler(self.entity[text[1:-1]])
            except KeyError:
                self._raiseerror("Undefined entity {}".format(text), code=11)

    def feed(self, data):
        self.parser.Parse(data, 0)

    def close(self):
        self.parser.Parse("", 1)
        try: close_handler = self.target.close
        except AttributeError: pass
        else: return close_handler()

