#!/usr/bin/python3

import note

import db, resultCache
import filedb
import collections
import sys,os

def disconnect(thing,nega):
    if thing and nega:
        note('removing',thing,nega)
        db.execute("UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT $1) WHERE ARRAY[id] <@ $2::bigint[]",(thing,nega))
        db.execute(
            "UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT unnest($1::bigint[])) WHERE id = $2",(nega,thing))


db.execute("SET work_mem TO 100000")

def tag(thing,tags):
    if not isinstance(tags,Taglist):
        derp = Taglist()
        try:
            derp.posi = set(tags)
        except OverflowError:
            print('???',tags)
            raise
        tags = derp
    implied = os.environ.get('tags')
    if implied:
        implied = parse(implied)
    with db.transaction():
        if tags.nega:
            if isinstance(list(tags.nega)[0],str):
                # XXX: should we cascade tag deletion somehow...? delete artist -> all artist tags ew no
                tags.nega = db.execute('SELECT id FROM tags WHERE name = ANY($1::text[])',(tags.nega,))
                tags.nega = [row[0] for row in tags.nega]
            elif hasattr(list(tags.nega)[0],'category'):
                tags.nega = [db.execute('SELECT id FROM tags WHERE name = $1 AND category = $2',(tag.name,tag.category))[0][0] for tag in tags.nega]

            if implied: 
                tags.update(implied)
                implied = None
            disconnect(thing,tags.nega)
        if tags.posi:
            if isinstance(list(tags.posi)[0],str):
                categories = collections.defaultdict(list)
                tags.posi = list(tags.posi)
                # note: do NOT set tags.posi since we still need them as string names
                ntags = tuple(set(row[0] for row in db.execute('SELECT findTag(name) FROM unnest($1::text[]) AS name',(tags.posi,))))
                for i in range(len(tags.posi)):
                    if ':' in tags.posi[i]:
                        category,name = tags.posi[i].split(':')
                        category = db.execute("SELECT findTag($1)",(category,))[0][0]
                        name = db.execute("SELECT findTag($1)",(name,))[0][0]
                        wholetag = ntags[i]
                        categories[category].append(wholetag)
                        # NOT connect(category,wholetag)
                        # XXX: ...until we can fix the search to be breadth first...?
                        db.execute("SELECT connectOne($1,$2)",(name,wholetag))
                        db.execute("SELECT connectOne($1,$2)",(wholetag,name))
                for category,ctags in categories.items():
                    db.execute("SELECT connectManyToOne($1,$2)",(ctags,category))
                tags.posi = ntags
            elif hasattr(list(tags.posi)[0],'category'):
                categories = collections.defaultdict(list)
                out = []
                for tag in tags.posi:
                    if tag.category is None:
                        whole = db.execute('SELECT findTag($1)',(tag.name,))[0][0]
                    else:
                        category = db.execute("SELECT findTag($1)",(tag.category,))[0][0]
                        name = db.execute('SELECT findTag($1)',(tag.name,))[0][0]
                        whole = db.execute('SELECT findTag($1)',(tag.category+':'+tag.name,))[0][0]
                        categories[category].append(whole)
                        db.execute("SELECT connectOne($1,$2)",(name,whole))
                        db.execute("SELECT connectOne($1,$2)",(whole,name))
                    out.append(whole)
                for category,stags in categories.items():
                    db.execute('SELECT connectManyToOne($1,$2)',(stags,category))
                tags.posi = out
            if implied: tags.update(implied)
            db.execute("SELECT connectOneToMany($1,$2)",(thing,tags.posi))
            db.execute("SELECT connectManyToOne($1,$2)",(tags.posi,thing))

class Taglist:
    def __init__(self):
        self.posi = set()
        self.nega = set()
    def update(self,bro):
        self.posi = set(self.posi)
        self.nega = set(self.nega)
        self.posi.update(bro.posi)
        self.nega.update(bro.nega)
        self.posi.difference_update(bro.nega)
        self.nega.difference_update(bro.posi)
    def __hash__(self):
        return hash((tuple(self.posi),tuple(self.nega)))
    def __repr__(self):
        return repr(('taglist',full(self.posi),full(self.nega)))
    def __str__(self):        
        friend = Taglist()
        friend.posi = self.posi
        friend.nega = self.nega
        names(friend)
        s = ', '.join(friend.posi)
        if friend.nega:
            if friend.posi:
                s += ', '
            s += ', '.join('-'+name for name in friend.nega)
        return s

def makeTag(name):
    try: 
        name = int(name)
        result = db.execute("SELECT id FROM tags WHERE id = $1",(name,))
        if not result:
            raise RuntimeError("No tag by the id "+str(name))
        return result[0][0]
    except ValueError: pass

    for attempt in range(3):
        result = db.execute("SELECT id FROM tags WHERE name = $1",(name,))
        if result: break
        result = db.execute("WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id) INSERT INTO tags (id,name) SELECT thing.id,$1 FROM thing RETURNING id",(name,))
    return result[0][0]

def getTag(name):
    result = db.execute("SELECT id FROM tags WHERE name = $1",(name,))
    if result: return result[0][0]
    return None

def _namesOneSide(tags):
    tags = list(tags)
    if not tags or type(tags[0])==str:
        return set(tags)
    names = set()
    if isinstance(tags[0],tuple):
        tags = tuple(tag[0] for tag in tags)
    note.yellow(tags)
    for row in db.execute('SELECT name FROM tags WHERE id = ANY($1)',(tags,)):
        names.add(str(row[0]))
    return names
def names(tags):
    if isinstance(tags,Taglist):
        tags.posi = _namesOneSide(tags.posi)
        tags.nega = _namesOneSide(tags.nega)
    else:
        # for related tags...
        tags = _namesOneSide(tags)
    return tags

def _fullOneSide(tags):
    tags = list(tags)
    if not tags or type(tags[0])==tuple:
        return set(tags)
    result = set()
    if isinstance(tags[0],str):
        field = 'name'
    else:
        field = 'id'
    for row in db.execute('SELECT id,name FROM tags WHERE '+field+' = ANY($1)',(tags,)):
        result.add(tuple(row))
    return result

def full(tags):
    if isinstance(tags,Taglist):
        tags.posi = _fullOneSide(tags.posi)
        tags.nega = _fullOneSide(tags.nega)
    else:
        tags = _fullOneSide(tags)
    return tags

def parse(s,create=True):
    tags = Taglist()
    for thing in s.split(','):
        thing = thing.strip()
        if thing[0] == '-':
            thing = thing[1:]
            tags.posi.discard(thing)
            tags.nega.add(thing)
        else:
            tags.posi.add(thing)
    if create:
        derp = makeTag
    else:
        derp = getTag
    tags.posi = set(tag for tag in
                    (derp(tag) for tag in tags.posi) if tag)
    tags.nega = set(tag for tag in
                    (derp(tag) for tag in tags.nega) if tag)
    tags.posi = tags.posi.difference(tags.nega)
    tags.nega = tags.nega.difference(tags.posi)
    return tags
if __name__ == '__main__':
    if len(sys.argv)==3:
        tag(int(sys.argv[1],0x10),parse(sys.argv[2:]))
        resultCache.clear()
    else:
        import gtkclipboardy as clipboardy
        from mygi import Gtk,Gdk,GObject,GLib
        window = Gtk.Window()
        window.connect('destroy',Gtk.main_quit)
        box = Gtk.VBox()
        window.add(box)
        tagentry = Gtk.Entry()
        gobutton = Gtk.ToggleButton(label='Go!')
        box.pack_start(tagentry,True,True,0)
        box.pack_start(gobutton,True,False,0)
        def gotPiece(piece):
            if not ( piece.startswith('http://[fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c]') or piece.startswith('http://cy.h')):
                return

            try: num = int(piece.rstrip('/').rsplit('/',1)[-1],0x10)
            except ValueError: return
            tags = [tag.strip(" \t") for tag in tagentry.get_text().split(',')]
            tag(num,parse(','.join(tags)))
            resultCache.clear()
        window.show_all()
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        clipboardy.run(gotPiece, lambda b: gobutton.get_active())

