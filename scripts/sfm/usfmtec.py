#!/usr/bin/env python3
'''
Convert the publishable vernacular text in a USFM file according to a given
.tec mapping file. In addition, support dictionary replacement, and automatic
case generation.
'''
__version__ = '0.2.1'
__date__ = '5 March 2020'
__author__ = 'Martin Hosken <martin_hosken@sil.org>'
__credits__ = '''\
Tim Eves provided the concordance program on which this is based.
'''

from palaso.sfm import usfm, style, Element, Text, generate
from palaso.teckit.engine import Converter, Mapping
from itertools import groupby, chain
import csv
import codecs
import glob
import optparse
import os.path
import re
import warnings
import sys
import unicodedata


class scrparser(usfm.parser):
    def _canonicalise_footnote(self, content):
        return content


def uni_unescape(s):
    return codecs.decode(s, 'raw_unicode_escape')


word_cat = {
    'Lu', 'Ll', 'Lt', 'Lm', 'Lo',
    'Mn', 'Mc', 'Me', 'Pd', 'Cs',
    'Co', 'Cn'
}

isletters = ""


def sfmmap(elements, elemente, textf, doc):
    def _g(e):
        if isinstance(e, Element):
            e = elements(e)
            e[0:] = list(map(_g, e))
            elemente(e)
            return e
        else:
            e_ = textf(e)
            return Text(e_, e.pos, e)
    return list(map(_g, doc))


def isword(char):
    if char in isletters:
        return True
    return unicodedata.category(char) in word_cat


def aswords(txt):
    ''' returns array of word forming, punc, word forming, punc '''
    g = [(i[0], "".join(i[1])) for i in groupby(txt, isword)]
    res = [i[1] for i in g]
    if not g[0][0]:
        res.insert(0, "")
    return res


class notec(object):
    def convert(self, txt, **kw): return txt


class pyconverter(object):
    def __init__(self, fname, fnname=None):
        self.vars = {}
        exec(compile(open(fname, "rb").read(), fname, 'exec'), self.vars)
        if fnname is None:
            fnname = self.vars.get('__converter__', None)
        if fnname is None or fnname not in self.vars:
            raise SyntaxError("Can't find %s in %s" % (fnname, fname))
        self.fn = self.vars[fnname]

    def convert(self, txt, **kw):
        return self.fn(txt)


class usfm_transducer(object):

    def __init__(self, case='', tec=notec(), opts={}):
        self.caps = [1]
        self.oquotes = uni_unescape(opts.openquotes)
        self.cquotes = uni_unescape(opts.closequotes)
        self.punc = uni_unescape(opts.sentencepunc)
        self.capquotes = (uni_unescape(opts.capitalopenquotes)
                          if opts.capitalopenquotes else self.oquotes)
        self.case = case
        self.enc = tec
        self.opts = opts
        self.tags = {}
        self.dict = {}
        self.phrases = {}
        self.phrase_keys = {}
        self.morphs = {}
        self.morph_keys = ''
        self.morphid = '!'
        if opts.capitaltags:
            self.ctags = set(opts.capitaltags.split())
        else:
            self.ctags = set()
        if opts.capitalalltags:
            self.calltags = set(opts.capitalalltags.split())
        else:
            self.calltags = set()
        if opts.normalize:
            self.normal = 'NF' + opts.normalize.upper()
        else:
            self.normal = None

    def load_dict(self, fname, incol, outcol, tagcol=-1, binary=False):
        morph_keys = []
        fh = open(fname, 'rt', encoding='latin_1' if binary else 'utf_8_sig')
        entries = csv.reader(fh, skipinitialspace=True)
        maxcol = max(incol, outcol, tagcol)
        for e in entries:
            if len(e) <= maxcol or (len(e[0]) and e[0][0] == "#"):
                continue
            k = self.enc.convert(e[incol], finished=True).strip()
            if k.find(self.morphid) != -1:     # has stem marker
                if k[0] != self.morphid:
                    mk = '^' + k
                else:
                    mk = k[1:]
                    k = k[1:]
                if k[-1] != self.morphid:
                    mk = mk + '$'
                else:
                    k = k[0:-1]
                    mk = mk[0:-1]
                morph_keys.append(mk)
                self.morphs[k] = e[outcol].strip()
            elif len(list(filter(isword, k))) != len(k):
                self.phrases[k] = e[outcol].strip()
            else:                              # dictionary entry
                self.dict[k] = e[outcol].strip()
            if tagcol >= 0 and e[tagcol]:  # has tag constraints
                self.tags[k] = set(e[tagcol].split())
        morph_keys.sort(key=len)
        self.morph_keys = "|".join(morph_keys)
        phrase_keys = sorted(self.phrases.keys(), key=len)
        for k in phrase_keys:
            p = aswords(k)
            if p[0] in self.phrase_keys:
                self.phrase_keys[p[0]].append(p)
            else:
                self.phrase_keys[p[0]] = [p]
        fh.close()

    def element_start(self, node):
        try:
            if node.meta.get('StyleType') == 'Note':
                self.caps.append(1)
        except KeyError as e:
            e.args = ("Element: %s at %r" % (node.name, node.pos), )
            raise e
        return node

    def element_end(self, node):
        try:
            if node.meta.get('StyleType') == 'Note':
                self.caps.pop()
        except KeyError as e:
            e.args = ("Element: %s at %r" % (node.name, node.pos), )
            raise e

    def convert_node(self, tnode):
        if tnode.parent and not (set(tnode.parent.meta['TextProperties'])
                                 & set(('publishable', 'vernacular'))):
            return tnode
        if (tnode.parent
            and ((tnode.parent.meta.get('StyleType') == 'Paragraph'
                  and tnode is tnode.parent[0])
                 or tnode.parent.name in self.ctags)):
            self.caps[-1] = 1
        self.tnode = tnode
        res = re.sub(r'[^\x00-\x1f]+', self.convert, tnode)
        if self.normal:
            res = unicodedata.normalize(self.normal, res)
        return res

    def convert(self, match):
        if self.opts.binary:
            input = match.group(0).encode('latin_1')
        else:
            input = match.group(0)
        res = self.enc.convert(input, finished=True)
        if res.strip() == '':
            return res
        if self.caps[-1]:
            res = re.sub(r'^([\s' + self.oquotes + r']*)(.)',
                         lambda m: m.group(1) + m.group(2).upper(), res)
        if re.search(f'[{self.punc}][{self.cquotes}]*\\s*$', res):
            self.caps[-1] = 1
        elif re.search(f'[{self.cquotes}]+\\s*$', res):
            pass
        elif re.match(r'^\s*\S', res):
            self.caps[-1] = 0
        parent_node = self.tnode.parent
        rlist = aswords(res)
        res = ""
        while len(rlist) > 0:
            rlen = len(rlist)
            wd = rlist.pop(0)
            if wd:
                case = wd[0].isupper()
                wd = wd[0].lower() + wd[1:]
                found = False
                if wd in self.phrase_keys:
                    for p in self.phrase_keys[wd]:
                        if len(p) <= rlen and p[1:] == rlist[0:len(p)-1]:
                            s = "".join(p)

                            if s in self.tags \
                                    and parent_node.name not in self.tags[s]:
                                continue
                            del rlist[0:len(p)-1]
                            wd = self.phrases[s]
                            found = True
                            break
                if (not found
                    and wd in self.dict
                    and (wd not in self.tags
                         or parent_node.name in self.tags[wd])):
                    wd = self.dict[wd] or wd
                    found = True
                elif self.morph_keys and not found:
                    def _g(m):
                        g = m.group(1)
                        if g not in self.tags \
                                or parent_node.name in self.tags[wd]:
                            g = self.morphs[g]
                        return g

                    wd = re.sub(f'(?iu)({self.morph_keys})', _g, wd)
                if case:
                    wd = wd[0].upper() + wd[1:]
            if len(rlist):
                res += wd + rlist.pop(0)
            else:
                res += wd

        res = re.sub(
            rf'([{self.punc}][{self.cquotes}\s]*[{self.oquotes}\s]*)(.)',
            lambda m: (m.group(1) + (m.group(2).upper()
                       if isword(m.group(2)[0])
                       else m.group(2))),
            res)

        if parent_node \
           and (parent_node.meta['TextType'] == 'Title'
                or parent_node.name in self.calltags) \
           and self.capquotes:
            res = re.sub(
                rf'(^\s*|\s)([{self.capquotes}]*)(.)',
                lambda m: (m.group(1) + m.group(2) + (m.group(3).upper()
                           if isword(m.group(3)[0])
                           else m.group(3))),
                res)
        elif self.capquotes:
            res = re.sub(
                f'(?<=[{self.capquotes}])([{self.oquotes}]*)(.)',
                lambda m: (m.group(1) + m.group(2).upper()
                           if isword(m.group(2)[0])
                           else m.group(1) + m.group(2)),
                res)

        if self.case:
            res = re.sub(
                self.case,
                lambda m: m.group(0)[0].upper() + m.group(0)[1:],
                res)
        return res


def transduce(fname, opts):
    def identity_mkr(*args): return args

    conv = usfm_transducer(case=opts.capitalise, opts=opts)
    if opts.tec:
        tec = Converter(Mapping(opts.tec), forward=not opts.reverse)
        conv.enc = tec
    elif opts.python:
        conv.enc = pyconverter(opts.python, opts.pythonfunc)

    if opts.dict:
        conv.load_dict(opts.dict, opts.dictinput, opts.dictoutput,
                       tagcol=opts.dicttag, binary=opts.binary)

    infh = codecs.open(fname, 'r', 'latin_1' if opts.binary else 'utf_8_sig')
    try:
        doc = sfmmap(conv.element_start, conv.element_end, conv.convert_node,
                     scrparser(infh,
                               stylesheet=opts.stylesheet,
                               error_level=opts.error_level))
    except SyntaxError as err:
        sys.stderr.write(parser.expand_prog_name(
            f'%prog: failed to parse USFM: {err!s}\n'))
        sys.exit(1)
    finally:
        infh.close()
    return doc


if __name__ == '__main__':
    parser = optparse.OptionParser(
        usage=f'%prog [options] <SFM FILE>\n{__doc__}')
    parser.set_defaults(
        sentencepunc=b".!?",
        openquotes=b"'\"\\u2018\\u201C\\[{(<\\u00AB",
        closequotes=b"'\"\\u2019\\u201D\\]})>\\u00BB")
    parser.add_option("-b", "--binary", action="store_true",
                      help="Input is legacy encoded, not Unicode")
    parser.add_option("-c", "--capitalise", action="store",
                      help="regular expression match which is capitalised")
    parser.add_option("--capitaltags", action="store",
                      help="list of tags to capitalise their contents")
    parser.add_option(
        "--capitalalltags", action="store",
        help="list of tags to capitalise each word in their contents")
    parser.add_option(
        "--openquotes", action="store",
        help="list of opening quote chars as a string with \\u escaping"
             " [default: %default]")
    parser.add_option(
        "--closequotes", action="store",
        help="list of closing quote chars as a string with \\u escaping"
             " [default: %default]")
    parser.add_option(
        "--sentencepunc", action="store",
        help="list of sentence final punctuation with \\u escaping"
             " [default: %default]")
    parser.add_option(
        "--capitalopenquotes", action="store",
        help="list of chars that force a new sentence"
             " [default value of --openquotes]")
    parser.add_option("--letters", action="store",
                      help="more word forming characters, with \\u escaping")
    parser.add_option("-d", "--dict", action="store", metavar='PATH',
                      help="CSV dictionary of input output replacements")
    parser.add_option(
        "--dict-input", action="store", type="int", dest="dictinput",
        default=0,
        help="Input column number (from 0) of CSV dictionary [%default]")
    parser.add_option(
        "--dict-output", action="store", type="int", dest="dictoutput",
        default=1,
        help="Output column number (from 0) of CSV dictionary [%default]")
    parser.add_option(
        "--dict-context", action="store", type="int", dest="dicttag",
        default=-1,
        help="Marker context column number (from o) of CSV dictionary. Cells"
             " contain a space separated list of required markers.")
    parser.add_option("-n", "--lines", action="store_true",
                      help="Don't parse as USFM, just as plain text")
    parser.add_option("-o", "--output", action="store", metavar='PATH',
                      help="Specify output file or directory")
    parser.add_option("-p", "--python", action="store", metavar='PATH',
                      help="Python file containing converter code")
    parser.add_option(
        "--pythonfunc", action="store",
        help="Function name within python file, to call to convert text")
    parser.add_option("-t", "--tec", action="store", metavar='PATH',
                      help="TECKit .tec file to use for conversion")
    parser.add_option("-r", "--reverse", action="store_true",
                      help="Run .tec file in reverse")
    parser.add_option("--normalize", action="store",
                      help="Unicode normalize converted text [c, d, kc, kd]")
    parser.add_option("-v", "--verbose", action='store_true', default=False,
                      help='Print out statistics and progress info')
    parser.add_option(
        "", "--no-warnings", action='store_false', dest='warnings',
        default=True,
        help='Silence syntax warnings discovered during SFM parsing')
    parser.add_option(
        "-s", "--strict", action='store_const', dest='error_level',
        const=usfm.ErrorLevel.Marker, default=usfm.ErrorLevel.Content,
        help='Turn on strict parsing mode. Markers not in the stylesheet or'
             ' private name space will cause an error')
    parser.add_option(
        "-l", "--loose", action='store_const', dest='error_level',
        const=usfm.ErrorLevel.Unrecoverable, default=usfm.ErrorLevel.Content,
        help='Turn on loose parsing mode. Nothing short of orphan markers or'
             ' unterminated inlines will halt the parser.')
    parser.add_option(
        "-S", "--stylesheet", action='store', type='string',
        metavar='PATH', default=None,
        help='User stylesheet to add/override marker definitions to the'
             ' default USFM stylesheet')
    parser.add_option("-V", "--version", action="store_true",
                      help="Print program version and exit")

    opts, sfms = parser.parse_args()

    if opts.version:
        sys.stdout.write(__version__+"\n")
        sys.exit(0)

    sfms = list(chain.from_iterable(map(glob.iglob, sfms)))
    if len(sfms) < 1:
        sys.stderr.write(parser.expand_prog_name('%prog: missing SFM FILE\n'))
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    for a in ('dict', 'output', 'python', 'tec'):
        if getattr(opts, a, None) is not None:
            setattr(opts, a, os.path.expanduser(getattr(opts, a)))

    if opts.stylesheet:
        stylesheet_path = os.path.expanduser(opts.stylesheet)
        opts.stylesheet = usfm.default_stylesheet.copy()
        opts.stylesheet.update(style.parse(open(stylesheet_path, 'r')))
    else:
        opts.stylesheet = usfm.default_stylesheet

    if opts.letters:
        isletters = uni_unescape(opts.letters)

    work = []
    first_def = -1
    if not opts.output:
        first_def = 0
    elif not os.path.isdir(opts.output):
        work.append((sfms[0], opts.output))
        first_def = 1
    else:
        work.extend(
            zip(sfms,
                (os.path.join(opts.output, os.path.split(x)[1]) for x  in sfms)))
    if first_def > -1:
        work.extend(zip(sfms[first_def:],
                        (f"{x}_u" for x in sfms[first_def:])))

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("always" if opts.warnings
                                  else "ignore", SyntaxWarning)
            for job in work:
                res = generate(transduce(job[0], opts))
                ofh = codecs.open(job[1], "w", "utf-8")
                ofh.write(res)
                ofh.close()

    except IOError as err:
        sys.stderr.write(
            parser.expand_prog_name(f'%prog: IO error: {err!s}\n'))
        sys.exit(2)
