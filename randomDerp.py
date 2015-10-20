import versions,db
import withtags,tags as tagsModule

from orm import IS,EQ,Select,OuterJoin,AND,AS,argbuilder,InnerJoin,Limit,Order,With

import random

v = versions.Versioner('random')

@v(version=1)
def initially():
    db.setup('''CREATE TABLE randomSeen (
    id SERIAL PRIMARY KEY,
    media bigint REFERENCES things(id),
    category integer DEFAULT 0,
    UNIQUE(media,category))''')

v.setup()

def churn(tags,limit=9):
    category = hash(tags) % 0x7FFFFFFF
    stmt,arg = withtags.tagStatement(tags,limit=limit)
    cat = arg(category)
    # [with.base] -> limit.clause -> order.clause -> select
    base = stmt.body if hasattr(stmt,'body') else stmt
    base = base.clause # order (.clause -> select)
    notSeen = IS('randomSeen.media','NULL')
    base.clause.where = AND(base.clause.where,notSeen) if base.clause.where else notSeen
    base.clause.From = OuterJoin(base.clause.From,
                                 AS(Select('media','randomSeen',
                                                                                 EQ('category',cat)),
                                    'randomSeen'),
                            EQ('randomSeen.media','media.id'))
    base.clause.what = ('media.id',cat)
    base.order = 'random(),'+arg(random.random())
    stmt = With(
        Select('count(*)','rows'),
        rows=(None,'INSERT INTO randomSeen (media, category) ' + stmt.sql() + '\nRETURNING 1')).sql()
    args = arg.args
    #print(stmt.replace('  ','.'))
    #print(args)
    #raise SystemExit

    while True:
        try:
            num = db.execute(stmt,args)[0][0]
        except db.ProgrammingError as e:
            derp = 0
            lines = stmt.split('\n')
            import math
            wid = int(1+math.log(len(lines)) / math.log(10))
            wid = '{:'+str(wid)+'}'
            def num():
                nonlocal derp
                ret = wid.format(derp)+' '
                derp += 1
                return ret
            print('\n'.join(num()+line for line in lines))
            print(e.info['message'].decode('utf-8'))
            raise SystemExit
        if num > 0: break
        # out of media, better throw some back into the pot
        with db.transaction():
            db.execute('DELETE FROM randomSeen WHERE category = $1 AND id < (SELECT AVG(id) FROM randomSeen WHERE category = $1)',(category,))
            # this shouldn't violate unique, since more than 1/2 were deleted
            # or... should it be SELECT MEDIAN(id) or something above?
            db.execute('UPDATE randomSeen SET id = id - (SELECT MIN(id) FROM randomSeen WHERE category = $1) WHERE category = $1',(category,))
            db.execute("SELECT setval('randomSeen_id_seq',(SELECT MAX(id) FROM randomSeen WHERE category = $1))",(category,))

    
def get(tags,offset=None,limit=9):
    category = hash(tags) % 0x7FFFFFFF
    arg = argbuilder()
    category = arg(category)
    stmt = Select(withtags.tagsWhat,InnerJoin(
                    'randomSeen',InnerJoin('media','things',EQ('things.id','media.id')),
        EQ('randomSeen.media','media.id')),
                  EQ('randomSeen.category',category))
    stmt = Order(stmt,'randomSeen.id DESC')
    stmt = Limit(stmt,offset=offset,limit=limit)
    rows = db.execute(stmt.sql(),arg.args)
    #print('\n'.join(r[0] for r in rows))
    #raise SystemExit
    return rows

from redirect import Redirect
import time
from filedb import oj
import filedb

try:
    with open(oj(filedb.base,'nope.tags'),'rt') as inp:
        nopeTags = tagsModule.parse(inp.read())
except IOError:
    nopeTags = None

def info(path,params):
    if 'o' in params:
        offset = int(params['o'][0])
        if offset == 0:
            offset = None
            del params['o']
    else:
        offset = None
    if 'q' in params:
        tags = tagsModule.parse(params['q'][0])
    else:
        tags = User.tags()
    if nopeTags: tags.update(nopeTags)
    if 'c' in params:
        #print(params)
        churn(tags,limit=1)
        zoop = {'t': str(time.time())}
        zoop.update((n,v[0]) for n,v in params.items() if n not in {'o','c'})
        zoop = urllib.parse.urlencode(zoop)
        raise Redirect('?'+zoop if zoop else '.',code=302)
    while True:
        links = get(tags,offset=offset)
        if links: return links
        churn(tags)

from user import User
from session import Session
from pages import makePage,makeLinks,makeLink,Links

import dirty.html as d
from tornado.gen import coroutine,Return
import urllib.parse

@coroutine
def page(info,path,params):
    with Links:
        info = list(info)
        id,name,type,tags = info.pop(0)
        #Links.next = "." this gets preloaded sometimes :/
        links = yield makeLinks(info)
        fid,link,thing = yield makeLink(id,type,name,False,0,0)
        zoop = {'c': '1'}
        zoop.update((n,v[0]) for n,v in params.items())
        zoop = urllib.parse.urlencode(zoop)
        zoop = '?' + zoop if zoop else '.'
        page = makePage(
            "Random",
                        d.p(d.a('Another?',href=zoop)),
                        d.p(d.a(link,href='/art/~page/'+fid+'/')),
            d.div(links if links else '',title='past ones'))
        raise Return(page)

if __name__ == '__main__':
    from pprint import pprint
    pprint(get(tags.parse('apple bloom, -sweetie belle, scootaloo')))
