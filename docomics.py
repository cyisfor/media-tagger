#!/usr/bin/python3
from message import MessageProcess, command, codecs
from multiprocessing import Process, Pipe

getting = False

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


class ComicMaker(MessageProcess):
    backend = False
    @command(codec=codecs.one.str,backend=True)
    def findMedium(self,source):
        assert self.backend
        import parse,db
        try:
            source = parse.normalize(source)
        except RuntimeError: pass
        source = cleanSource(source)
        print('source?', source)

        while True:
            res = db.execute('SELECT media.id FROM media,urisources WHERE uri = $1 AND sources @> ARRAY[urisources.id]',(source,))
            if res:
                self.foundMedium(res[0][0])
                break
            else:
                try:
                    parse.parse(source)
                    continue
                except Exception as e:
                    self.errorFindingMedium(e,source)
                    break
    @command(codec=codecs.str,backend=True,codecs={3:codecs.one.num})
    def create(self,title,description,source,medium):
        if source is not None:
            s = db.execute('SELECT id FROM urisources WHERE uri = $1',(source,))
            if s:
                source = s[0][0]
            else:
                s = db.execute('WITH derp AS (INSERT INTO sources DEFAULT VALUES RETURNING id) INSERT INTO urisources (id,uri,code) SELECT id,$1,200 FROM derp RETURNING urisources.id',(source,))
                source = s[0][0]
            assert(source)

            comic = db.execute('INSERT INTO comics (title,description,source) VALUES ($1,$2,$3) RETURNING id',(
                title,
                desc,
                source))
        else:
           comic = db.execute('INSERT INTO comics (title,description) VALUES ($1,$2)',(
               title,
               desc))
        self.comic = comic[0][0]
        self.which = 0
        self.setPage(medium,self.comic,self.which)
    @command(codec=codecs.num,backend=True)
    def setPage(self,medium,comic,which):
        db.execute('SELECT setComicPage($1,$2,$3)',(medium,comic,which))
        self.pageSet(comic,which)
    @command(codec=codecs.num,backend=False)
    def pageSet(self,comic,which):
        self.page.set_text('{:x}'.format(which+1))
        self.comic.set_text('{:x}'.format(comic))
        self.getting = False
    def start(self):
        # this is in the main (GUI) process
        super().start()
        self.clipqueue = []
        try:
            import pgi
            pgi.install_as_gi()
        except ImportError: pass
        import gtkclipboardy as clipboardy
        window = Gtk.Window()
        window.connect('destroy',self.quit)
        box = Gtk.VBox()
        window.add(box)

        self.comic = Gtk.Entry()
        box.pack_start(label("Comic",self.comic),True,True,0)
        self.page = Gtk.Entry()
        box.pack_start(label("Page",self.page),True,True,0)

        self.gobutton = Gtk.ToggleButton(label='Go!')
        box.pack_start(self.gobutton,True,False,0)
        self.gobutton.connect('toggled',lambda e: checkInitialized(None))

        window.show_all()
        start,run = clipboardy.make(self.clipboardYanked,self.notGetting)
        # run inside start? because this is starting the other process
        # then running as this one.
        run()
    def notGetting(self):
        return not self.getting
    def createComic(self,com,medium):
        from gi.repository import Gtk
        def label(name,entry):
            box = Gtk.HBox()
            box.pack_start(Gtk.Label(name),True,True,0)
            box.pack_start(entry,True,True,0)
            return box
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

            source = sourceEntry.get_text() or None
            self.create(title,desc,source,medium)
            win.destroy()
        titleEntry.connect('activate',onActivate)
        descEntry.connect('activate',onActivate)
        sourceEntry.connect('activate',onActivate)

        win.show_all()
    @command(codec=codecs.one.str,backend=False)
    def errorFindingMedium(self,err,source):
        dl = Gtk.MessageDialog(
            window,
            0,
            Gtk.MessageType.ERROR,
            Gtk.ButtonsType.OK_CANCEL,
            err)
        def andle(dialog,response):
            dialog.destroy()
            if response == Gtk.ResponseType.OK:
                # back to the backend with ye!
                self.findMedium(source)
            else:
                self.getting = False
                self.quit()
        dl.connect('response',andle)
        dl.show_all()
    def quit(self):
        assert not self.backend
        self.terminate()
        self.join()
        Gtk.main_quit()
    def clipboardYanked(self,source):
        if not self.gobutton.get_active():
            return
        self.clipqueue.append(source)
        if self.getting:
            print('getting',self.clipqueue)
            return
        self.getting = True
        self.nextSource()
    def nextSource(self):
        if not self.clipqueue:
            self.getting = False
            return
        source = self.clipqueue.pop(0)
        try: self.foundMedium(mine(source))
        except ValueError as e: pass
        self.findMedium(source)
    pendingMedium = None
    @command(codec=codecs.one.num)
    def foundMedium(self,medium):
        assert not self.backend
        self.pendingMedium = medium
        print('yay',medium)
        try:
            comic = int(self.comic.get_text(),0x10)
            page = int(self.page.get_text(),0x10)
        except ValueError:
            self.checkInitialized(medium)
            return
        with db.transaction():
            if db.execute('SELECT count(id) FROM comics WHERE id = $1',(com,))[0][0] == 0:
                self.createComic(comic,medium)
            else:
                self.setPage(medium,comic,page)
    @command(backend=True,codec=codecs.nothing)
    def maxComic(self):
        self.setMaxComic(db.execute('SELECT MAX(id) + 1 FROM comics')[0][0])
    @command(backend=False,codec=codecs.one.num)
    def setMaxComic(self,comic):
        if self.comic.get_text() == '':
            self.comic.set_text('{:x}'.format(comic))
            
    @command(backend=True,codec=codecs.one.num)
    def maxPage(self,comic):
        self.setMaxPage(db.execute('SELECT MAX(which) + 1 FROM comicPage WHERE comic = $1',(comic,)))
    @command(backend=False,codec=codecs.one.num)
    def setMaxPage(self,page):
        if self.page.get_text() == '':
            self.page.set_text('{:x}'.format(page))                    
    def checkInitialized(self,medium):
        # TODO: optional arguments by passing None
        # so that you can pass medium around, w/out it being
        # in the protocol when you're not passing it around.
        # ...probably better to just recalculate it?
        comic = self.comic.get_text()
        if not comic:
            return self.findMaxComic(medium)        
        page = self.page.get_text()
        if not page:
            return self.findMaxPage(int(comic,0x10))
def main():
    global comic,page,gobutton,window
if __name__ == '__main__': main()
