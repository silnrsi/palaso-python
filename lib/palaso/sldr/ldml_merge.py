# -*- coding: utf-8
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the University nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

from palaso.sldr.ldml import Ldml
import os

try:
    basestring
    string_types = basestring
except NameError:
    string_types = str

class _arrayDict(dict):
    def set(self, k, v):
        if k not in self:
            self[k] = []
        self[k].append(v)

    def pop(self, k, v=None):
        if k not in self: return v
        res = self[k].pop()
        if not len(self[k]): del self[k]
        return res

    def remove(self, k, v):
        if k not in self: return
        self[k].remove(v)
        if not len(self[k]): del self[k]


class LdmlMerge(Ldml):

    def difference(self, other, this=None):
        """Strip out from self, everything that is in other, if the values are the same."""
        if this == None: this = self.root
        other = getattr(other, 'root', other)
        # if empty elements, test .text and all the attributes
        if not len(other) and not len(this):
            return (other.contentHash == this.contentHash)
        for o in other:
            for t in filter(lambda x: x.attrHash == o.attrHash, this):
                if o.contentHash == t.contentHash or (o.tag not in self.blocks and self.difference(o, this=t)):
                    if hasattr(t, 'alternates') and hasattr(o, 'alternates'):
                        for (k, v) in o.alternates:
                            if k in t.alternates and v.contentHash == t.alternates[k].contentHash:
                                del t.alternates[k]
                        if len(t.alternates) == 0:
                            this.remove(t)
                    else:
                        this.remove(t)
                break
        return not len(this) and (not this.text or this.text == other.text)

    def overlay(self, other, usedrafts=False, this=None):
        """Add missing information in self from other. Honours @draft attributes"""
        if this == None: this = self.root
        other = getattr(other, 'root', other)
        for o in other:
            # simple if for now, if more use a dict
            if o.tag == '{'+self.silns+'}external-resources':
                self._overlay_external_resources(o, this, usedrafts)
            else:
                self._overlay_child(o, this, usedrafts)

    def _overlay_child(self, o, this, usedrafts):
        addme = True
        for t in filter(lambda x: x.attrHash == o.attrHash, this):
            addme = False
            if o.contentHash != t.contentHash:
                if o.tag not in self.blocks:
                    self.overlay(o, usedrafts=usedrafts, this=t)
                elif usedrafts:
                    self._merge_leaf(other, t, o)
                if t.text == "↑↑↑" and o.text != "":
                    t.text = o.text
            break  # only do one alignment
        if addme and (o.tag != "alias" or not len(this)):  # alias in effect turns it into blocking
            this.append(o)

    def _overlay_external_resources(self, other, this, usedrafts):
        """Handle sil:font fallback mechanism"""
        silfonttag = '{'+self.silns+'}font'
        fonts = []
        this = list(filter(lambda x: x.attrHash == other.attrHash, this))[0]
        for t in list(this):
            if t.tag == silfonttag:
                fonts.append(t)
                this.remove(t)
        for o in other:
            if o.tag == silfonttag:
                types = o.get('types', '').split(' ')
                if not len(types):
                    types = ['default']
                for t in types:
                    if t == 'default':
                        fonts = []
                        break
                    else:
                        for f in fonts:
                            tt = f.get('types', 'default').split(' ')
                            if t in tt:
                                f.set('types', " ".join(filter(lambda x: x != t, tt)))
                        fonts = filter(lambda x: x.get('types', '') != '', fonts)
                this.append(o)
            else:
                self._overlay_child(o, this, usedrafts)
        for f in fonts:
            this.append(f)

    def flag_nonroots(self):
        """ Add @sil:modified="true" to collation elements"""
        for n in self.root.findall('collations/collation'):
            n.set('{'+self.silns+'}modified', 'true')

    def _merge_leaf(self, other, b, o):
        """Handle @draft and @alt"""
        if not hasattr(o, 'alternates'): return
        if hasattr(b, 'alternates'):
            for (k, v) in o.items():
                if k not in b.alternates: b.alternates[k] = v
        else:
            b.alternates = o.alternates
            
    def _align(self, this, other, base):
        """Internal method to merge() that aligns elements in base and other to this and
           records the results in this. O(7N)"""
        olist = dict(map(lambda x: (x.contentHash, x), other)) if other is not None else {}
        blist = dict(map(lambda x: (x.contentHash, x), base)) if base is not None else {}
        for t in list(this):
            t.mergeOther = olist.get(t.contentHash, None)
            t.mergeBase = blist.get(t.contentHash, None)
            if t.mergeOther is not None:
                del olist[t.contentHash]
                if t.mergeBase is not None:
                    del blist[t.contentHash]
            elif t.mergeBase is not None:
                del blist[t.contentHash]
        odict = _arrayDict()
        for v in olist.values(): odict.set(v.attrHash, v)
        if base is not None:
            bdict = _arrayDict()
            for v in blist.values(): bdict.set(v.attrHash, v)
        for t in filter(lambda x: x.mergeOther == None, this):     # go over everything not yet associated
            # this is pretty horrible - find first alignment on key attributes. (sufficient for ldml)
            t.mergeOther = odict.pop(t.attrHash)
            if t.mergeOther is not None:
                del olist[t.mergeOther.contentHash]
            if t.mergeBase is None and base is not None:
                if t.mergeOther is not None and t.mergeOther.contentHash in blist:
                    t.mergeBase = blist.pop(t.mergeOther.contentHash)
                    if t.mergeBase is not None: bdict.remove(t.mergeBase.attrHash, t.mergeBase)
                if t.mergeBase is None:
                    t.mergeBase = bdict.pop(t.attrHash)
                    if t.mergeBase is not None: del blist[t.mergeBase.contentHash]
        for e in olist.values():       # pick up stuff in other but not in this
            newe = self.copynode(e, this.parent)
            if base is not None and e.contentHash in blist:
                newe.mergeBase = blist.pop(e.contentHash)
            elif base is not None:
                newe.mergeBase = bdict.pop(e.attrHash)
                while newe.mergeBase is not None and newe.mergeBase.contentHash not in blist:
                    newe.mergeBase = bdict.pop(e.attrHash)
                if newe.mergeBase is not None:
                    del blist[newe.mergeBase.contentHash]
            else:
                newe.mergeBase = None
            newe.mergeOther = None     # don't do anything with this in merge()
            this.append(newe)

    def _merge_with_alts(self, base, other, target, default=None, copycomments=None):
        """3-way merge the alternates putting the results in target. Assumes target content is the required ending content"""
        res = False
        if default is None:
            default = base.default_draft
        # if base != target && base better than target
        if base is not None and base.contentHash != target.contentHash and (base.text or base.tag in self.blocks) and self.get_draft(base) < self.get_draft(target, default):
            res = True
            self._add_alt(base, target, default=default)  # add target as alt of target
            target[:] = base                                # replace content of target
            for a in ('text', 'contentHash', 'comments', 'commentsafter'):
                if hasattr(base, a):
                    setattr(target, a, getattr(base, a, None))
                elif hasattr(target, a):
                    delattr(target, a)
            if 'alt' in target.attrib:
                del target.attrib['alt']
            if self.get_draft(base) != target.document.default_draft:
                target.set('draft', _alldrafts[self.get_draft(base)])
        elif base is None and other is not None and other.contentHash != target.contentHash and (target.text or target.tag in self.blocks):
            res = True
            if self.get_draft(target, default) < self.get_draft(other, default):
                self._add_alt(target, other, default=default)
            else:
                self._add_alt(other, target, default=default)
                target[:] = other
                for a in ('text', 'contentHash', 'comments', 'commentsafter'):
                    if hasattr(other, a):
                        setattr(target, a, getattr(other, a, None))
                    elif hasattr(target, a):
                        delattr(target, a)
                if 'alt' in target.attrib:
                    del target.attrib['alt']
                if self.get_draft(other) != target.document.default_draft:
                    target.set('draft', _alldrafts[self.get_draft(other)])
        elif copycomments is not None:
            commentsource = base if copycomments == 'base' else other
            if comentsource is not None:
                for a in ('comments', 'commentsafter'):
                    if hasattr(commentsource, a):
                        setattr(target, a, getattr(commentsource, a))
                    elif hasattr(target, a):
                        delattr(target, a)
        res |= self._merge_alts(base, other, target, default)
        return res

    def _merge_alts(self, base, other, target, default='unconfirmed'):
        if other is None or not hasattr(other, 'alternates'): return False
        res = False
        if not hasattr(target, 'alternates'):
            target.alternates = dict(other.alternates)
            return (len(target.alternates) != 0)
        balt = getattr(base, 'alternates', {}) if base is not None else {}
        allkeys = set(balt.keys() + target.alternates.keys() + other.alternates.keys())
        for k in allkeys:
            if k not in balt:
                if k not in other.alternates: continue
                if k not in target.alternates or self.get_draft(target.alternates[k], default) > self.get_draft(other.alternates, default):
                    target.alternates[k] = other.alternates[k]
                    res = True
            elif k not in other.alternates:
                if k not in target.alternates or self.get_draft(target.alternates[k], default) > self.get_draft(balt[k]):
                    target.alternates[k] = balt[k]
                    res = True
            elif k not in target.alternates:
                if k not in other.alternates or self.get_draft(other.alternates[k], default) > self.get_draft(balt[k]):
                    target.alternates[k] = balt[k]
                else:
                    target.alternates[k] = other.alternates[k]
                res = True
            elif self.get_draft(target.alternates[k], default) > self.get_draft(other.alternates[k], default):
                target.alternates[k] = other.alternates[k]
                res = True
            elif self.get_draft(target.alternates[k], default) > self.get_draft(balt[k]):
                target.alternates[k] = balt[k]
                res = True
            elif other.alternates[k].contentHash != balt[k].contentHash:
                target.alternates[k] = other.alternates[k]
                res = True
        return res

    
    def _add_alt(self, target, origin, default='unconfirmed'):
        self._add_alt_leaf(target, origin.copy(),
                default=default, leaf=origin.contentHash is not None,
                alt = self.alt())

    def merge(self, other, base, this=None, default=None, copycomments=None):
        """ Does 3 way merging of self/this and other against a common base. O(N), base or other can be None.
            Returns True if any changes were made."""
        res = False
        if this == None: this = self.root
        if other is not None and hasattr(other, 'root'): other = other.root
        if base is not None and hasattr(base, 'root'): base = base.root
        self._align(this, other, base)
        # other and base can be None
        for t in list(this):       # go through children merging them
            if t.mergeBase is None:
                if self.useDrafts and t.mergeOther is not None and t.mergeOther.contentHash != t.contentHash:
                    self._merge_with_alts(t.mergeBase, t.mergeOther, t, default=default, copycomments=copycomments)
                continue
            if t.mergeOther is not None and t.mergeOther.contentHash != t.contentHash:     # other differs
                if t.mergeBase.contentHash == t.contentHash:   # base doesn't
                    if self.useDrafts:
                        res |= self._merge_with_alts(t.mergeBase, t.mergeOther, t, default=default, copycomments=copycomments)
                    else:
                        this.remove(t)                                  # swap us out
                        this.append(t.mergeOther)
                        res = True
                elif t.mergeBase.contentHash != t.mergeOther.contentHash:
                    res |= self.merge(t.mergeOther, t.mergeBase, t)        # could be a clash so recurse
                elif self.useDrafts:       # base == other
                    res |= self._merge_with_alts(t.mergeBase, t.mergeOther, t, default=default, copycomments=copycomments)
            elif t.mergeOther is None and t.mergeBase.contentHash == t.contentHash:
                this.remove(t)
                res = True
            elif self.useDrafts:
                res |= self._merge_with_alts(t.mergeBase, t.mergeOther, t, default=default, copycomments=copycomments)
        if base is not None and this.text == base.text:
            if other is not None:
                res = res or (this.text != other.text)
                this.text = other.text
                this.contentHash = other.contentHash
            elif this.text is not None:
                res = True
                this.text = None
                this.contentHash = None
            if self.useDrafts: res |= self._merge_with_alts(base, other, this, default=default, copycomments=copycomments)
        elif base is not None and other is not None and other.text != base.text:
            self.clash_text(this.text, other.text, (base.text if base is not None else None),
                                        this, other, base, usedrafts=self.useDrafts)
            if self.useDrafts:
                res |= self._merge_with_alts(base, other, this, default=default, copycomments=copycomments)
                return res
        elif self.useDrafts:
            res |= self._merge_with_alts(base, other, this, default=default, copycomments=copycomments)
        oattrs = set(other.keys() if other is not None else [])
        for k in this.keys():                                  # go through our attributes
            if k in oattrs:
                if k in base.attrib and base.get(k) == this.get(k) and this.get(k) != other.get(k):
                    res = True
                    this.set(k, other.get(k))                       # t == b && t != o
                elif this.get(k) != other.get(k):
                    self.clash_attrib(k, this.get(k), other.get(k), base.get(k), this, other, base, usedrafts=self.useDrafts)    # t != o
                    res = True
                oattrs.remove(k)
            elif base is not None and k in base.attrib:                        # o deleted it
                this.attrib.pop(k)
                res = True
        for k in oattrs:                                       # attributes in o not in t
            if base is None or k not in base.attrib or base.get(k) != other.get(k):
                this.set(k, other.get(k))                           # if new in o or o changed it and we deleted it
                res = True
        return res

    def clash_text(self, ttext, otext, btext, this, other, base, usedrafts = False, default=None):
        if usedrafts:
            if default is None:
                default = self.default_draft
            bdraft = self.get_draft(base)
            tdraft = self.get_draft(this)
            odraft = self.get_draft(other)
            if tdraft < odraft:
                self._add_alt(this, other, default=default)
                return
            elif odraft < tdraft:
                self._add_alt(this, this, default=default)
                this.text = otext
                this.contentHash = other.contentHash
                return
            elif tdraft >= bdraft:
                self._add_alt(this, this, default=default)
                self._add_alt(this, other, default=default)
                this.text = btext
                this.contentHash = base.contentHash
                return
        if not hasattr(this, 'comments'): this.comments = []
        this.comments.append('Clash: "{}" or "{}" from "{}"'.format(ttext, otext, btext))

    def clash_attrib(self, key, tval, oval, bval, this, other, base, usedrafts = False):
        if not hasattr(this, 'comments'): this.comments = []
        this.comments.append('Attribute ({}) clash: "{}" or "{}" from "{}"'.format(key, tval, oval, bval))
        return tval        # not sure what to do here. 'We' win!


def getldml(lname, dirs, **kw):
    for d in dirs:
        f = os.path.join(d, lname + '.xml')
        if os.path.exists(f):
            return LdmlMerge(f, **kw)
        f = os.path.join(d, lname[0].lower(), lname + '.xml')
        if os.path.exists(f):
            return LdmlMerge(f, **kw)
    return None

def flattenlocale(lname, dirs=[], rev='f', changed=set(),
                  skipstubs=False, fname=None, flattencollation=False, resolveAlias=False):
    """ Flattens an ldml file by filling in missing details from the fallback chain.
        If rev true, then do the opposite and unflatten a flat LDML file by removing
        everything that is the same in the fallback chain.
        changed contains an optional set of locales that if present says that the operation
        is only applied if one or more of the fallback locales are in the changed set.
        Values for rev: f - flatten, r - unflatten, c - copy"""
    def trimtag(s):
        r = s.rfind('_')
        if r < 0:
            return ''
        else:
            return s[:r]

    if isinstance(lname, Ldml):
        l = lname
        lname = fname
    elif not isinstance(lname, string_types):
        l = LdmlMerge(lname)
        lname = fname
    else:
        l = getldml(lname, dirs)
    if l is None: return l
    if skipstubs and len(l.root) == 1 and l.root[0].tag == 'identity': return None
    if rev != 'c':
        fallbacks = l.get_parent_locales(lname)
        if not len(fallbacks):
            fallbacks = [trimtag(lname)]
        if 'root' not in fallbacks and lname != 'root':
            fallbacks += ['root']
        if len(changed):       # check against changed
            dome = False
            for f in fallbacks:
                if f in changed:
                    dome = True
                    break
            if not dome: return None
        dome = True
        for f in fallbacks:    # apply each fallback
            while len(f):
                o = getldml(f, dirs)
                if o is not None:
                    if rev == 'r':
                        l.difference(o)
                        dome = False
                        break   # only need one for unflatten
                    else:
                        if f == 'root':
                            l.flag_nonroots()
                        l.overlay(o)
                f = trimtag(f)
            if not dome: break
    if resolveAlias:
        l.resolve_aliases()
    if skipstubs and len(l.root) == 1 and l.root[0].tag == 'identity': return None
    if flattencollation:
        collmap = {'phonebk' : 'phonebook'}
        def getcollator(lang, coll):
            try:
                if l.fname.endswith(lang+'.xml'):
                    c = l
                else:
                    c = getldml(('root' if lang == 'und' else lang), dirs)
                col = c.root.find('collations/collation[@type="{}"]/cr'.format(collmap.get(coll, coll)))
                return col.text
            except:
                return ''
            
        for i in l.root.findall('collations/collation/cr'):
            i.text = l.flatten_collation(i.text, getcollator)

    return l

if __name__ == '__main__':
    import sys, codecs
    l = LdmlMerge(sys.argv[1])
    if len(sys.argv) > 2:
        for f in sys.argv[2:]:
            if f.startswith('-'):
                o = LdmlMerge(f[1:])
                l.difference(o)
            else:
                o = LdmlMerge(f)
                l.overlay(o)
    l.normalise()
    sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)
    l.serialize_xml(sys.stdout.write) #, topns=False)

