#!/usr/bin/env python3
from mercurial import ui, commands
from mercurial import hg as _hg
from mercurial.utils.dateutil import datestr
import os, subprocess, re

def backquote(cmd) :
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()[0].strip()

class hg :
    def __init__(self, dir) :
        self.dir = dir
        cdir = os.getcwd()
        os.chdir(self.dir)
        self.repo = _hg.repository(ui.ui(), dir)
        self.repo.ui.quiet = True
        os.chdir(cdir)
        self.tip = len(self.repo)
        self.needs_attention = False

    def update(self) :
        try :
            commands.pull(self.repo.ui, self.repo, update = 1)
        except :
            self.needs_attention = True

    def recent_changes(self) :
        res = []
        for c in range(self.tip, len(self.repo)) :
            change = list(self.repo[c].changeset());
            change[0] = "".join(f"{ord(y)}:02X" for y in change[0][:6]).upper()
            change[2] = datestr(change[2], b"%y-%m-%d %H:%M:%S %1%2 (%a, %d %b %Y)")
            res.append(change)
        return res

class svn :
    def __init__(self, dir) :
        self.dir = dir
        cdir = os.getcwd()
        os.chdir(dir)
        self.tip = int(re.sub(b"[^0-9].*", b"", backquote('svnversion')))
        os.chdir(cdir)

    def update(self) :
        cdir = os.getcwd()
        os.chdir(self.dir)
        backquote('svn update')
        os.chdir(cdir)

    def recent_changes(self) :
        res = []
        cdir = os.getcwd()
        os.chdir(self.dir)
        currver = re.sub(b"[^0-9].*", b"", backquote('svnversion'))
        if int(currver) > self.tip :
            log = backquote('svn log -r ' + str(self.tip) + ':' + currver.decode('utf8'))
            state = ""
            change = []
            for line in log.splitlines() :
                if line.startswith(b'------') :
                    if state == "description" :
                        res.append(change)
                    change = []
                    state = "init"
                elif state == "init" :
                    change.extend(line.split(b" | "))
                    state = "postinit"
                elif state == "postinit" :
                    change.extend(["", ""])
                    state = "description"
                elif state == "description" :
                    if len(change[4]) : change[4] += "\n"
                    change[4] += line
            if state == "description" :
                res.append(change)
        os.chdir(cdir)
        return res

class git :
    def __init__(self, dir) :
        self.dir = dir
        cdir = os.getcwd()
        os.chdir(dir)
        self.tip = backquote('git show --pretty=format:%h')
        os.chdir(cdir)
    def update(self) :
        cdir = os.getcwd()
        os.chdir(self.dir)
        backquote('git pull')
        os.chdir(cdir)
    def recent_changes(self) :
        res = []
        cdir = os.getcwd()
        os.chdir(self.dir)
        currev = backquote('git show --pretty=format:%h')
        if not currev == self.tip :
            cmdstr = f"git log {self.tip}..{currev}"
            log = backquote(cmdstr)
            print(cmdstr)
            state = ""
            change = []
            for l in log.splitlines() :
                if l.startswith(b'commit') :
                    if state == "descripton" :
                        res.append(change)
                    state = ""
                    change = [l[7:12]]
                elif l.startswith(b'Author:') :
                    change.append(l[8:])
                elif l.startswith(b'Date:') :
                    change.append(l[8:])
                    change.append(b"")
                elif state == "" and l == "" :
                    state = "description"
                    change.append(b"")
                elif change[-1] == "" :
                    change[-1] = l
                else :
                    change[-1] = change[-1] + b"\n" + l
            if state == "description" :
                res.append(change)
        os.chdir(cdir)
        return res


def main():
    from optparse import OptionParser
    import gi
    gi.require_versions({'Gtk':'3.0', 'WebKit2':'4.0'})
    from gi.repository import Gtk
    from gi.repository import WebKit2

    htmlhdr="""
    <?xml version="1.0"?>
    <html>
    <body>
    """

    htmlftr="""
    </body>
    </html>
    """

    parser = OptionParser()
    parser.set_defaults(list = str(os.path.expanduser("~/.config/vcsaggro/vcsaggro.cfg")))
    parser.add_option("-l", "--list", help = "List of directories to aggregate [~/.config/vcsaggro/vcsaggro.cfg]")
    parser.add_option("-d", "--debug", action = "store_true", help = "do internal testing")
    (options, args) = parser.parse_args()

    info = []
    htmlstr = ""
    if os.path.exists(options.list) :
        res = []
        flist = open(options.list)
        for dir in (os.path.expanduser(ln.strip()) for ln in flist.readlines()) :
            vcs = None
            if not os.path.exists(dir) : continue
            print(dir)
            if os.path.exists(os.path.join(dir, ".hg")) :
                vcs = hg(dir)
            elif os.path.exists(os.path.join(dir, ".svn")) :
                vcs = svn(dir)
            elif os.path.exists(os.path.join(dir, ".git")) :
                vcs = git(dir)
            if vcs :
                if options.debug :
                    vcs.tip -= 1
                else :
                    vcs.update()
                res = vcs.recent_changes()
            if len(res) :
                info.append((dir, res))

    for dir, changes in info :
        htmlstr += (f'\n<h2>{dir!s}</h2>\n'
                    '<table cellspacing="10">\n')
        for c in changes :
            htmlstr += (f'\n<tr>'
                        f'<td>{" ".join(c[2].split(" ")[0:2])!s}</td>'
                        f'<td>{c[0]!s}</td>'
                        f'<td>{c[1]!s}</td>'
                        f'<td>{c[4]!s}</td>'
                        '</tr>\n')
        htmlstr += "</table>\n"

    if htmlstr != "" :
        base = Gtk.Window()
        scroll = Gtk.ScrolledWindow()
        view = WebKit2.WebView()
        view.load_html_string(htmlhdr + htmlstr + htmlftr, "home")
        scroll.add(view)
        base.add(scroll)
        base.set_default_size(750, 400)
        base.connect('delete-event', Gtk.main_quit)
        base.show_all()
        Gtk.main()


if __name__ == "__main__":
    main()
