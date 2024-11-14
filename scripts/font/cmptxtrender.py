#!/usr/bin/env python3

import codecs
from palaso.font.shape import make_shaper
from difflib import SequenceMatcher
from fontTools.ttLib import TTFont
import sys, os, os.path, shutil, re, argparse
import json
import json.encoder
from xml.etree.ElementTree import parse
import csv

tables = {
    'gr' : ('GDEF', 'GSUB', 'GPOS'),
    'ot' : ('Gloc', 'Glat', 'Silf', 'Sill', 'Feat'),
    'hb' : (),
    'hbot' : ('Gloc', 'Glat', 'Silf', 'Sill', 'Feat'),
    'icu' : ('Gloc', 'Glat', 'Silf', 'Sill', 'Feat')
}
tables['uhb'] = tables['ot']

def roundfloat(f, res) :
    try :
        return(int(f / res) * res)
    except ValueError :
        pass
    return 0

def roundpt(pt, res) :
    try :
        return(int(pt[0] / res) * res, int(pt[1] / res) * res)
    except ValueError :
        pass
    return (0, 0)

def name_mapping(filename):
    glyph_data = dict()
    if not os.path.exists(filename):
        print(f'WARNING: {filename} does not exist')
        return glyph_data
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        if 'glyph_name' not in reader.fieldnames:
            return glyph_data
        if 'ps_name' not in reader.fieldnames:
            return glyph_data
        for row in reader:
            glyph_name = row['glyph_name']
            ps_name = row['ps_name']
            if glyph_name == '':
                glyph_name = ps_name
            glyph_data[ps_name] = glyph_name
    return glyph_data

def name(tt, gl, rounding = 0.1) :
    if gl[0] is None :
        x = "_adv_"
    elif gl[0] != 0 :
        ps = tt.getGlyphName(gl[0])
        x = glyph_data.get(ps, ps)
    else :
        x = "0:{:04X}".format(gl[2])
    return (x, roundfloat(gl[1][0], rounding), roundfloat(gl[1][1], rounding))

def cmaplookup(tt, c) :
    cmap = tt.getBestCmap()
    if cmap:
        ps = cmap.get(ord(c), '.notdef')
        return glyph_data.get(ps, ps)
    return '.nocmap'

def makelabel(name, line, word) :
    if name :
        if word > 1 :
            return "{} {}".format(name, word)
        else :
            return name
    else :
        return "{}.{}".format(line, word)

def ftostr(x, dp=2) :
    res = ("{:." + str(dp) + "f}").format(x)
    if res.endswith("." + ("0" * dp)) :
        res = res[:-dp-1]
    else :
        res = re.sub(r"0*$", "", res)
    return res

# Have the JSONEncoder use ftostr to render floats to 2dp rather than lots
json.encoder.FLOAT_REPR=ftostr

def strpoint(p) :
    return "("+",".join(map(ftostr, p))+")"

class HTMLLog(object) :
    def __init__(self, f, fpaths, args, inputs) :
        self.out = f
        self.opts = args
        temps = ("""
    @font-face {{
        font-family: testfont{1};
        src: url('{0}');
    }}
    .text{1} {{
        font-family: testfont{1};
    }}""",
                """<tr><td>{2}:</td><td>{3}</td></tr>
""")
        _strs = []
        for i in range(len(fpaths)) :
            _strs.append([x.format(fpaths[i], i+1, args.label[i], inputs[i]) for x in temps])
        strs = ["".join(x) for x in zip(*_strs)]
        
        self.out.write("""<html><head>
<meta charset="UTF8"/>
<style>
    {0[0]}
    .eq {{
        font-family: monospace;
        color: black;
        vertical-align: text-top;
    }}
    .neq {{
        font-family: monospace;
        color: red;
        vertical-align: text-top;
    }}
    table, th, td {{
        border-collapse: collapse;
        border: 1px solid grey;
        padding: 5px;
    }}
</style></head><body>
<table>
    {0[1]}
    <tr><td>Test document:</td><td>{1}</td></tr>
    <tr><td>Engine:</td><td>{2}</td></tr>
    <tr><td>Language:</td><td>{3}</td></tr>
    <tr><td>Script:</td><td>{4}</td></tr>
    <tr><td>Features:</td><td>{5}</td></tr>
</table>
<p/>
<table>
""".format( strs,
                args.text,
                args.engine, 
                args.lang if args.lang != 0 else '', 
                args.script if args.script != 0 else '', 
                ", ".join(args.feat if args.feat is not None else [])))
        if args.label is not None and len(args.label) :
            self.out.write("<tr><th></th><th>Original</th><th>{}</th>".format(args.label[0]))
            for i in range(1, len(args.label)) :
                self.out.write("<th>{0}</th><th>{1}</th><th>{1}</th>".format(args.label[0], args.label[i]))
            self.out.write("<th>style</th>")
            self.out.write("</tr>\n")

    def style(self, g, c = 'neq') :
        return "<span class='{}'>{}:\t{}</span>".format(c, g[0], ftostr(g[1]), ftostr(g[2]))

    def _diffpos(self, l, r, lprev, rprev) :
        res = [("<span class='eq'>{}:\t(</span>".format(l[0]), "<span class='eq'>{}:\t(</span>".format(r[0]))]
        for i in range(1, 3) :
            s = ',' if i == 1 else ')'
            c = 'eq' if l[i] - lprev[i] == r[i] - rprev[i] else 'neq'
            u = []
            for t in (l[i], r[i]) :
                u.append("<span class='{}'>{}</span>{}".format(c, ftostr(t), s))
            res.append(u)
        return ["".join(x) for x in zip(*res)]

    def logentry(self, label, linenumber, wordnumber, string, gglyphs, bases, lang, feats) :
        # Language from command line arguments
        langstr = " lang='{}'".format(self.opts.lang) if self.opts.lang else ""

        # Language and user features from FTML files
        features = [] # for formatting the string with features
        styles = [] # for displaying the styles (language and/or features) used
        if lang:
            langstr = " lang='{}'".format(lang)
            styles.append(lang)
        if feats:
            for k in sorted(feats):
                v = feats[k]
                features.append('"{0}" {1}'.format(k, v))
                styles.append('_'.join([k, str(v)]))
        featstr = " style='font-feature-settings: " + ", ".join(features) + "'" if len(features) > 0 else ''
        style = '_'.join(styles)

        # If there is no style information use the language argument if it was specified
        if style == '' and langstr:
            style = self.opts.lang

        self.out.write("  <tr><td>{5} {0}.{1}</td><td class='eq'>{4}</td><td class='text1'{3}{6}>{2}</td>\n".format(linenumber, wordnumber, string, langstr, "<br/>".join(x[0] for x in bases), label, featstr))
        if len(gglyphs) < 2 :
            self.out.write("    <td class='eq'>{0}</td>\n".format("<br/>".join("{}:\t({},{})".format(x[0], ftostr(x[1]), ftostr(x[2])) for x in gglyphs[0])))
            self.out.write("    </tr>\n")
            return

        def getname(t) :
            return str(t[0])
        for l in range(1, len(gglyphs)) :
            s = SequenceMatcher(None, [getname(x) for x in gglyphs[0]], [getname(x) for x in gglyphs[l]])
            info = []
            lprev = (0, 0, 0)
            rprev = (0, 0, 0)
            for o in s.get_opcodes() :
                if o[0] == 'insert' :
                    for i in range(o[3], o[4]) :
                        info.append(('', self.style(gglyphs[l][i])))
                elif o[0] == 'delete' :
                    for i in range(o[1], o[2]) :
                        info.append((self.style(gglyphs[0][i]), ''))
                elif o[0] == 'replace' :
                    for i in range(o[1], o[2]) :
                        info.append((self.style(gglyphs[0][i]), self.style(gglyphs[l][i-o[1]+o[3]]) if i-o[1]+o[3] < o[4] else ''))
                    for i in range(o[3] + o[2] - o[1], o[4]) :
                        info.append(('', self.style(gglyphs[l][i])))
                else :
                    for i in range(o[1], o[2]) :
                        info.append(self._diffpos(gglyphs[0][i], gglyphs[l][i-o[1]+o[3]], lprev, rprev))
                        lprev = gglyphs[0][i]
                        rprev = gglyphs[l][i-o[1]+o[3]]
            for inf in zip(*info) :
                self.out.write("    <td class='eq'>{}</td>\n".format("<br/>".join(inf)))
            self.out.write("    <td class='text{0}'{2}{3}>{1}</td>\n".format(l+1, string, langstr, featstr))
            self.out.write("    <td>{0}</td>\n".format(style))
        self.out.write("  </tr>\n")

    def logend(self) :
        self.out.write("</body></html>\n");

class JsonLog(object) :
    def __init__(self, f, fpaths, args, inputs) :
        self.out = f
        self.opts = args
        self.out.write("{\n")
        self.encoder = json.JSONEncoder()

    def logentry(self, label, linenumber, wordnumber, string, gglyphs, bases, lang, feats) :
        s = makelabel(label, linenumber, wordnumber)
        self.out.write('\"'+s+'\" : ')
        # have to use iterencode here to get json.encoder.FLOAT_REP to work
        #res = "\n".join(map(lambda x : "".join(self.encoder.iterencode([(g[0], roundpt(g[1], 0.01)) for g in x])), gglyphs))
        res = "".join(self.encoder.iterencode(gglyphs))
        self.out.write(res)
        self.out.write(',\n')

    def logend(self) :
        self.out.write('"":[]}\n')

def dosafecopy(inf, outf, opts, i) :
    pid = os.getpid()
    while os.path.exists(outf+str(pid)) :
        pid += 1
    outlocal = outf + str(pid)
    if opts.strip :
        f = TTFont(inf)
        for t in tables[opts.engine[i] if i < len(opts.engine) else opts.engine[-1]] :
            try :
                del f[t]
            except KeyError :
                pass # deleting a non-existing table is not an error
        f.save(outlocal)
        f.close()
    else :
        shutil.copy2(inf, outlocal)
    try :
        os.rename(outlocal, outf)
    except OSError :
        pass    # don't care if it fails, assuming something else copied it first

def docopy(f, opts, i) :
    # this code is fraught with collision possibilities given there may be 8 runs going simultaneously
    dname = os.path.join(os.path.dirname(opts.output), opts.copy + str(i) + opts.engine[i])
    fname = os.path.join(dname, os.path.basename(f))
    doit = False
    if not os.path.exists(fname) :
        doit = True
        if not os.path.exists(dname) :
            try :
                os.makedirs(dname)
            except OSError as e:
                if e.errno != 17 : raise e     # race condition, job done already
    else :
        bstat = os.stat(f)
        nstat = os.stat(fname)
        if bstat.st_ctime > nstat.st_ctime :
            doit = True
    if doit :
        dosafecopy(f, fname, opts, i)
    return fname

outputtypes = {
    'html' : HTMLLog,
    'json' : JsonLog
}

def LineReader(infile, spliton=None) :
    f = codecs.open(infile, encoding="utf_8")
    for l in f.readlines() :
        #l = l.rstrip("\n")
        l = l[:-1]
        if spliton is not None :
            res = (None, l.split(spliton), None, None, 0)
        else :
            res = (None, (l, ), None, None, 0)
        yield res

def FtmlReader(infile, spliton=None) :
    etree = parse(infile)
    styles = {}
    for s in etree.iter('style'):
        l = s.get("lang", None)
        feats = {}
        for f in s.get("feats", "").split(","):
            m = re.match(r"^\s*'([^']+)'\s+(\d|on|off)\s*$", f)
            if not m:
                continue
            k = m.group(1)
            v = m.group(2)
            v = int({"on": 1, "off": 0}.get(v, v))
            feats[k] = v
        n = s.get("name")
        styles[n] = [l, feats]
    for e in etree.iter('test') :
        l = e.get('label', "")
        s = e.find('string')
        res = []
        style = styles.get(e.get("stylename", ""), None)
        t = re.sub(r"\\u([0-9a-fA-F]{4,6})", lambda m: chr(int(m.group(1), 16)), "".join(s.itertext()))
        if spliton is not None:
            res.extend((l, t.split(spliton)))
        else :
            res.extend((l, (t, )))
        res += style if style is not None else [None, None]
        res += [1] if e.get('rtl', False) else [0]
        yield res


texttypes = {
    'txt' : LineReader,
    'ftml' : FtmlReader,
    'xml' : FtmlReader
}

parser = argparse.ArgumentParser(description='''If the first font is above the output
file in the filesystem hierarchy, it may not load.
On firefox, ensure that the configuration option security.fileuri.strict_origin_policy
is set to false to allow locally loaded html files to access fonts anywhere on the
local filesystem. Alternatively use --copy to copy the font and reference that.''')
parser.add_argument("infonts",nargs="+",help="Input fonts")
parser.add_argument("-t","--text",help="text file to test each line from")
parser.add_argument("-o","--output",help="file to log results to")
parser.add_argument("-f","--feat",action="append",help="id=value pairs, may be repeated")
parser.add_argument("-e","--engine",action="append",help="renderer(s) to use (ot,*gr,hb,icu). Repeatable")
parser.add_argument("-l","--lang",help="language to tag text with")
parser.add_argument("-s","--script",action="append",help="script of text")
parser.add_argument("-r","--rtl",action="store_true",help="right to left")
parser.add_argument("-k","--keep",action="store_true",help="keep going, don't return error count")
parser.add_argument("-p","--split",action="store_true",help="Split on spaces")
parser.add_argument("-L","--label",action="append",help="report font labels")
parser.add_argument("-S","--strip",action="store_true",help="Strips smart code other than needed by engine, when copying font")
parser.add_argument("-g","--glyphdata",action="store",help="CSV file for glyph name mappings")
parser.add_argument("--copy",help="Make a conditional copy of infont1 to the given directory relative to the output directory so that the html does not have to look up in the filesystem hierarchy to find the font. The relative directory is suffixed by the font index (1, 2)")
parser.add_argument("--outputtype",help="Type of output file [*html, json]")
parser.add_argument("--texttype",help="Type of text input file else taken from text file extension")
parser.add_argument("-V","--verbose",action="store_true",help="Give progress indicator")
opts = parser.parse_args()

if not opts.lang : opts.lang = 0
if opts.script is None : opts.script = []
if not len(opts.script) : opts.script.append(0)
if not opts.rtl : opts.rtl = 0
if not opts.engine or not len(opts.engine) : opts.engine = ['gr']
if os.getenv('CTR_UHB') == '1':
    opts.engine = [engine.replace('ot', 'uhb') for engine in opts.engine]
if sys.version_info.major > 2:
    outfile = open(opts.output, "w") if opts.output else sys.stdout
elif opts.output :
    outfile = codecs.open(opts.output, mode="w", encoding="utf_8")
else :
#    outfile = codecs.EncodedFile(sys.stdout, "unicode_internal", file_encoding="utf_8")
    outfile = codecs.getwriter("utf_8")(sys.stdout)

if not opts.label : opts.label = ["Input font{}".format(x+1) for x in range(len(opts.infonts))]
if not opts.outputtype : opts.outputtype = 'html'
if not opts.texttype :
    (_, ext) = os.path.splitext(opts.text) if opts.text is not None else ('', '.txt')
    opts.texttype = ext[1:]
if opts.split : spliton = ' '
else : spliton = None

feats = {}
if opts.feat :
    for f in opts.feat :
        k, v = f.split('=')
        feats[k.strip()] = int(v.strip())

origargs = []
if opts.copy and opts.output :
    for i in range(len(opts.infonts)) :
        origargs.append(opts.infonts[i])
        opts.infonts[i] = docopy(opts.infonts[i], opts, i)
else :
    origargs = opts.infonts
fpaths = [os.path.relpath(x, start=(os.path.dirname(opts.output) if opts.output else '.')) for x in opts.infonts]

glyph_data = dict()
if opts.glyphdata:
    glyph_data = name_mapping(opts.glyphdata)

fonts = []
tts = []
for i in range(len(opts.infonts)) :
    while len(opts.engine) <= i :
        opts.engine.append(opts.engine[-1])
    while len(opts.script) <= i :
        opts.script.append(opts.script[-1])
    fonts.append(make_shaper(opts.engine[i], opts.infonts[i], 0, opts.rtl, feats, opts.script[i], opts.lang))
    tts.append(TTFont(opts.infonts[i].encode('utf_8')))
reader = texttypes[opts.texttype](opts.text, spliton)

count = 0
errors = 0
log = None
for label, words, lang, feats, direction in reader :
    if words[0] is None : continue
    count += 1
    wcount = 0
    for s in words :
        wcount += 1
        if opts.verbose:
            sys.stdout.write("{}\r".format(wcount))
            sys.stdout.flush()
            print(s.encode("unicode_escape"))
        gls = [[name(tts[0], x) for x in fonts[0].glyphs(s, includewidth=True, lang=lang, feats=feats, trace=opts.verbose, dir=direction)]]
        if gls[-1][-1][0] is None:
            gls[-1][-1] = ('_adv_', gls[-1][-1][1], gls[-1][-1][2])
        logme = len(fonts) < 2
        for i in range(1, len(fonts)) :
            gls.append([name(tts[i], x) for x in fonts[i].glyphs(s, includewidth=True, lang=lang, feats=feats, dir=direction)])
            if gls[-1][-1][0] is None:
                gls[-1][-1] = ('_adv_', gls[-1][-1][1], gls[-1][-1][2])
            if gls[-1] != gls[0]:
                logme = True
        if logme :
            if log is None :
                log = outputtypes.get(opts.outputtype, HTMLLog)(outfile, fpaths, opts, opts.infonts)
            bases = [(cmaplookup(tts[0], x), (0,0)) for x in s]
            log.logentry(label, count, wcount, s, gls, bases, lang, feats)
            errors += 1
if log is not None : log.logend()
outfile.close()
sys.exit(0 if opts.keep else errors)
