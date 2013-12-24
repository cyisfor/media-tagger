import user as derp
import withtags
import db

def user(path,params):
    params = dict(params)
    rescale = params.get('rescale')
    if rescale:
        rescale = rescale[0]
        if rescale:
            rescale = True
        else:
            rescale = False
    else:
        rescale = False
    news = {'rescaleimages': rescale}
    newtags = params.get('tags')    
    news['defaultTags'] = False
    
    self = derp.currentUser()
    with db.transaction():
        # XXX: tasteless
        db.c.execute("DELETE FROM uzertags WHERE uzer = $1",(self.id,))

        if newtags and newtags[0] and len(newtags[0]) > 0:
            tags = withtags.parse(newtags[0].decode('utf-8'))
            print('oy',(tags))
            if tags.posi:
                db.c.execute('INSERT INTO uzertags (id,uzer,nega) SELECT unnest(array(SELECT unnest($1::bigint[]) EXCEPT SELECT id FROM uzertags WHERE uzer = $2)),$2,FALSE',(tags.posi,self.id))
            if tags.nega:
                db.c.execute('INSERT INTO uzertags (id,uzer,nega) SELECT unnest(array(SELECT unnest($1::bigint[]) EXCEPT SELECT id FROM uzertags WHERE uzer = $2)),$2,TRUE',(tags.nega,self.id))
        db.c.execute('UPDATE uzers SET defaultTags = FALSE WHERE id = $1',(self.id,))
    derp.set(news.items())
    return ""
