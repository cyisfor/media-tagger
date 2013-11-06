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
    if newtags and not newtags[0] == 0:
        news['noDefaultTags'] = True
    derp.set(news.items())
    
    self = derp.currentUser()
    # XXX: tasteless
    db.c.execute("DELETE FROM uzertags WHERE uzer = $1",(self.id,))

    if newtags and newtags[0] and len(newtags[0]) > 0:
        tags,negatags = withtags.parse(newtags[0].decode('utf-8'))
        if len(tags) == 0 and len(negatags) == 0:
            # must be a syntax error
            return ''
        print('oy',(tags,negatags))
        if tags:
            db.c.execute('INSERT INTO uzertags (id,uzer,nega) SELECT unnest($1::bigint[]),$2,FALSE',(tags,self.id))
        if negatags:
            db.c.execute('INSERT INTO uzertags (id,uzer,nega) SELECT unnest($1::bigint[]),$2,TRUE',(negatags,self.id))
    return ""
