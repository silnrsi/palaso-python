
from xml.etree.ElementTree import parse

def read_any(elem) :
    if elem.tag == "dict" : return read_dict(elem)
    elif elem.tag == "array" : return read_array(elem)
    elif elem.tag == 'string' : return elem.text

def read_dict(elem) :
    res = {}
    for k, v in zip(elem[::2], elem[1::2]) :
        res[k.text] = read_any(v)
    return res

def read_array(elem) :
    return map(read_any, elem)

def read_robofab_glyphlist(libfname, contentsfname) :
    etree = parse(libfname)
    glist = None
    for e in etree.getroot().iterfind('dict') :
        d = read_any(e)
        if "org.robofab.glyphOrder" in d :
            glist = d["org.robofab.glyphOrder"]
    if not glist : return
    etree = parse(contentsfname)
    files = {}
    for e in etree.getroot().iterfind("dict") :
        d = read_any(e)
    f = file(contentsfname, "w")
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
""")
    for g in glist :
        f.write("""        <key>{0}</key>
        <string>{1}</string>
""".format(g, d[g]))

    f.write("""</dict>
</plist>
""")

