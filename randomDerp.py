import versions,db
import withtags,tags

from orm import IS,EQ,Select,OuterJoin,AND,AS,argbuilder

v = versions.Versioner('random')

@v(version=1)
def initially():
    db.setup('''CREATE TABLE randomSeen (
    id SERIAL PRIMARY KEY,
    media bigint REFERENCES things(id),
    category integer DEFAULT 0,
    UNIQUE(media,category))''')

v.setup()

def tagsfor(idents):
    print("\n".join(i[0] for i in db.execute('''EXPLAIN SELECT things.id,array(SELECT tags.name FROM tags INNER JOIN (SELECT unnest(neighbors)) AS neigh ON neigh.unnest = tags.id)
    FROM things WHERE things.id = ANY($1)''',(idents,))))
    raise SystemExit
    print('ident',idents)
    tags = [row for row in db.execute('SELECT things.id,array_agg(name) FROM tags INNER JOIN things ON ARRAY[tags.id] <@ things.neighbors WHERE ARRAY[things.id] <@ $1 GROUP BY things.id',(idents,))]
    print('tags',len(tags))
    return tags

def churn(tags,limit=0x3):
    category = hash(tags) % 0x7FFFFFFF
    print(category)
    stmt,arg = withtags.tagStatement(tags,limit=limit)
    category = arg(category)
    # [with.base] -> limit.clause -> order.clause -> select
    base = stmt.body if hasattr(stmt,'body') else stmt
    base = base.clause # order (.clause -> select)
    notSeen = IS('randomSeen.media','NULL')
    base.clause.where = AND(base.clause.where,notSeen) if base.clause.where else notSeen
    base.clause.From = OuterJoin(base.clause.From,
                                 AS(Select('media','randomSeen',
                                                                                 EQ('category',category)),
                                    'randomSeen'),
                            EQ('randomSeen.media','media.id'))
    base.clause.what = ('media.id',category)
    base.order = 'random()'
    stmt = 'INSERT INTO randomSeen (media, category) ' + stmt.sql() + '\nRETURNING count(media.id)'
    args = arg.args
    print(stmt.replace('  ','.'))
    print(args)

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
            db.execute('UPDATE randomSeen SET id = id - (SELECT MIN(id) FROM randomSeen WHERE category = $1) WHERE category = $1',(category,))
            db.execute("SELECT setval('randomSeen_id_seq',(SELECT MAX(id) FROM randomSeen WHERE category = $1)",(category,))

    
def get(tags,limit=0x3):
    category = hash(tags) % 0x7FFFFFFF
    print(category)
    arg = argbuilder()
    category = arg(category)
    stmt = Select(withtags.tagsWhat,InnerJoin(
        'randomSeen','media',
        EQ('randomSeen.media','media.id')),
                  EQ('randomSeen.category',category))
    rows = db.execute(stmt.sql(),arg.args)
    #print('\n'.join(r[0] for r in rows))
    #raise SystemExit
    return rows

def info(path,params):
    return get(tags.parse(params['q']) if 'q' in params else tags.Taglist())

from user import User
import dirty.html as d
from pages import makePage,makeLinks,makeLink,Links

from tornado.gen import coroutine,Return

@coroutine
def page(info,path,params):
    with Links:
        info = list(info)
        id,name,type,tags = info.pop(0)
        Links.next = "."
        links = yield makeLinks(info)
        fid,link,thing = yield makeLink(id,type,name,False,0,0)
        page = makePage(
            "Random",
            d.p(d.a(link,href=thing),
                d.img(src=thing)),
            d.div('moar',links if links else ''))
        raise Return(page)

if __name__ == '__main__':
    from pprint import pprint
    pprint(get(tags.parse('apple bloom, -sweetie belle, scootaloo')))
