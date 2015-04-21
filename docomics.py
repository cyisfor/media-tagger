#!/usr/bin/python3
from message import MessageProcess, Command, codec
from multiprocessing import Process, Pipe

class ComicMaker(MessageProcess):
    @Command(arguments=codec.num)
    def setup(self,comic,which):
        self.comic = comic
        self.which = which
    @Command(codec=codec.onestr)
    def newpage(self,source):
        source = 
        while True:
            res = db.execute('SELECT media.id FROM media,urisources WHERE uri = $1 AND sources @> ARRAY[urisources.id]',(parse.normalize(source),))
            if res:
                self.gotsource(res[0][0])
                break
            else:
                try:
                    parse.parse(source)
                    continue
                except Exception as e:
                    self.error(e)
                    break
    @Command(codecs={'default': codec.str, 2: codec.num})
    def create(self,title,description,source=None):
        if source:
            s = db.execute('SELECT id FROM urisources WHERE uri = $1',(source,))
            if s:
                source = s[0][0]
            else:
                s = db.execute('WITH derp AS (INSERT INTO sources DEFAULT VALUES RETURNING id) INSERT INTO urisources (id,uri,code) SELECT id,$1,200 FROM derp RETURNING urisources.id',(source,))
                source = s[0][0]
            assert(source)
        else:
            source = None

        if source is not None:
           db.execute('INSERT INTO comics (title,description,source) VALUES ($1,$2,$3)',(
               title,
               desc,
               source))
        else:
           db.execute('INSERT INTO comics (title,description) VALUES ($1,$2)',(
               title,
               desc))

    def gotsource(self,id):
        
        
try:
    import pgi
    pgi.install_as_gi()
except ImportError: pass

import db,sys,os
import urllib.parse

import gtkclipboardy as clipboardy
from gi.repository import Gtk,Gdk,GObject,GLib

comic = None
page = None
gobutton = None
window = None


def label(name,entry):
    box = Gtk.HBox()
    box.pack_start(Gtk.Label(name),True,True,0)
    box.pack_start(entry,True,True,0)
    return box

def createComic(com,created):
    builder = Gtk.Builder()
    message = "Please Give Comic {:x}'s Info".format(com)
    win = Gtk.Dialog()
    win.set_title(message)

    titleEntry = Gtk.Entry()
    descEntry = Gtk.Entry()
    sourceEntry = Gtk.Entry()

    action_area = win.get_internal_child(builder,"action_area")
    vbox = Gtk.VBox()
    action_area.pack_start(vbox,True,True,0)
    vbox.pack_start(Gtk.Label(message),True,True,0)
    vbox.pack_start(label('Title',titleEntry),True,True,0)
    vbox.pack_start(label('Description',descEntry),True,True,0)
    vbox.pack_start(label('Source',sourceEntry),True,True,0)


    def onActivate(e):
        title = titleEntry.get_text()
        desc = descEntry.get_text()
        print('activateboo',title,desc)
        if not title and desc: return

        source = sourceEntry.get_text()
        comicMaker.create(title,desc,source)
        win.destroy()
        created()
    titleEntry.connect('activate',onActivate)
    descEntry.connect('activate',onActivate)
    sourceEntry.connect('activate',onActivate)

    win.show_all()

sourceFinder = SourceFinder()
sourceFinder.start()

def findBySource(source,foundSource,fail):
    try:
        res = sourceFinder.check(source)
        print('found source ',source,res)
        foundSource(res)
    except Exception as e:
        dl = Gtk.MessageDialog(window,0,Gtk.MessageType.ERROR,Gtk.ButtonsType.OK_CANCEL,str(e))
        def andle(dialog,response):
            dialog.destroy()
            if response == Gtk.ResponseType.OK:
                findBySource(source,foundSource,fail)
            else:
                fail()
        dl.connect('response',andle)
        dl.show_all()

getting = False

def notGetting(text):
    return not getting

def cleanSource(url):
    return url.split('?',1)[0]

def mine(url):
    url = urllib.parse.urlparse(url)
    if url.scheme == 'http':
        if not url.netloc in {'[::1]','127.0.0.1','[fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c]','cy.h','cy.meshwith.me'}:
            raise ValueError('not cjdns derp')
    else:
        raise ValueError('not checking https derp')
    return int(url.path.rstrip('/').rsplit('/',1)[-1],0x10)

def gotMedium(medium,pageSet=None):
    global getting
    if getting:
        print('getting',medium)
        return
    getting = True
    if not gobutton.get_active():
        getting = False
        return

    def haveMedium(medium):
        print('yay',medium)
        try:
            com = int(comic.get_text(),0x10)
            pag = int(page.get_text(),0x10)
        except ValueError:
            checkInitialized()
            return
        def setPage():
            global getting
            db.execute('SELECT setComicPage($1,$2,$3)',(medium,com,pag))
            page.set_text('{:x}'.format(pag+1))
            getting = False
            if pageSet: pageSet()
        with db.transaction():
            if db.execute('SELECT count(id) FROM comics WHERE id = $1',(com,))[0][0] == 0:
                createComic(com,setPage)
            else:
                setPage()

    if isinstance(medium,int):
        haveMedium(medium)
    else:
        try: return haveMedium(mine(medium))
        except ValueError as e: pass
        try:
            medium = parse.normalize(medium)
        except RuntimeError: pass
        print('source?', medium)
        def fail():
            global getting
            getting = False

        def foundSource(res):
            if res:
                haveMedium(res)
            else:
                try: haveMedium(mine(medium))
                except ValueError: return
        findBySource(cleanSource(medium),foundSource,fail)

def checkInitialized(e=None):
    com = comic.get_text()
    if com:
        com = int(com,0x10)
    else:
        com = db.execute('SELECT MAX(id) + 1 FROM comics')[0][0]
        comic.set_text('{:x}'.format(com))
    pag = page.get_text()
    if pag == '':
        pag = db.execute('SELECT MAX(which) + 1 FROM comicPage WHERE comic = $1',(com,))
        if pag:
            pag = pag[0][0]
            if not pag:
                pag = 0
        else:
            pag = 0
        page.set_text('{:x}'.format(pag))
def main():
    global comic,page,gobutton,window
    window = Gtk.Window()
    window.connect('destroy',Gtk.main_quit)
    box = Gtk.VBox()
    window.add(box)

    comic = Gtk.Entry()
    box.pack_start(label("Comic",comic),True,True,0)
    page = Gtk.Entry()
    box.pack_start(label("Page",page),True,True,0)

    gobutton = Gtk.ToggleButton(label='Go!')
    box.pack_start(gobutton,True,False,0)
    gobutton.connect('toggled',checkInitialized)

    window.show_all()
    start,run = clipboardy.make(gotMedium,notGetting)
    run()
if __name__ == '__main__': main()
