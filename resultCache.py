# SELECT id FROM -> CREATE TABLE FROM SELECT etc

import db

import hashlib,base64

db.setup(*db.source("sql/resultCache.sql",False))

def encache(query,args,docache=True):
    #db.c.verbose = True
    with db.transaction():
        name = hashlib.sha1()
        name.update(query.encode('utf-8'))
        if hasattr(args,'values'):
            vals = sorted(n+str(v) for n,v in args.items())
        else:
            args = list(args)
            vals = args
        for arg in vals:
            name.update(str(arg).encode('utf-8'))
        name = base64.b64encode(name.digest(),altchars=b'-_').decode().replace('=','')
        if docache == False:
            return db.execute(query,args)
        try: 
            with db.saved():
                db.execute('CREATE TABLE resultCache."q'+name+'" AS '+query,args)
                db.execute('SELECT resultCache.updateQuery($1)',(name,))
        except db.ProgrammingError as e:
            if not 'already exists' in e.info['message'].decode('utf-8'): raise
        db.retransaction()
        return db.execute('SELECT * FROM resultCache."q'+name+'"')

def clear():
    while True:
        result = db.execute('SELECT resultCache.expireQueries()')[0][0];
        print('cleared',result,'results')
        if result < 1000: break
