
"""FontForge support module"""

def addAnchorClass(font, name, type = "base") :
    """ Adds a new anchor class to a font, if it is not already added.
        If necessary, it will create a lookup to hold the anchor in.

        Optionally type gives the type of attachment: base, mark, cursive

        Returns: name of sublookup containing the anchor
"""
    types = {
        "base" : "gpos_mark2base",
        "mark" : "gpos_mark2mark",
        "cursive" : "gpos_cursive"
    }
    try:
        sub = font.getSubtableOfAnchor(name)
        return sub
    except EnvironmentError :
        addClass = True

    try:
        lkp = font.getLookupInfo("_holdAnchors" + type)
    except:
        font.addLookup("_holdAnchors" + type, (types[type]), (), ())
        font.addLookupSubtable("_holdAnchors" + type, "_someAnchors" + type)

    font.addAnchorClass("_someAnchors" + type, name)
    return "_someAnchors" + type


