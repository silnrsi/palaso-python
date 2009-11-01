
"""FontForge support module"""

def addAnchorClass(font, name) :
    """ Adds a new anchor class to a font, if it is not already added.
        If necessary, it will create a lookup to hold the anchor in.

        Returns: name of sublookup containing the anchor
"""
    try:
        sub = font.getSubtableOfAnchor(name)
        return sub
    except EnvironmentError :
        addClass = True

    try:
        lkp = font.getLookupInfo("_holdAnchors")
    except:
        font.addLookup("_holdAnchors", ("gpos_mark2base"), (), ())
        font.addLookupSubtable("_holdAnchors", "_someAnchors")

    font.addAnchorClass("_someAnchors", name)
    return "_someAnchors"


