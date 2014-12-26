# SELECT id FROM -> CREATE TABLE FROM SELECT etc

import db

import hashlib,base64

db.setup("CREATE SCHEMA IF NOT EXISTS resultCache",

'''CREATE TABLE resultCache.queries(
        id SERIAL PRIMARY KEY,
        digest TEXT UNIQUE,
        created timestamptz DEFAULT clock_timestamp())''',

'''CREATE OR REPLACE FUNCTION resultCache.updateQuery(_digest text) RETURNS void AS
$$
BEGIN
    LOOP
        UPDATE resultCache.queries SET created = clock_timestamp() WHERE digest = _digest;
        IF found THEN
            RETURN;
        END IF;
        BEGIN
            INSERT INTO resultCache.queries (digest) VALUES (_digest);
        EXCEPTION
            WHEN unique_violation THEN
                -- do nothing
        END;
    END LOOP;
END;
$$ language 'plpgsql'
''',
'''CREATE OR REPLACE FUNCTION resultCache.expireQueries() RETURNS void AS
$$
DECLARE
_digest text;
BEGIN
    FOR _digest IN DELETE FROM resultCache.queries RETURNING digest LOOP
        BEGIN
            EXECUTE 'DROP TABLE resultCache."q' || _digest || '"';
        EXCEPTION
            WHEN undefined_table THEN
                -- do nothing
        END;
    END LOOP;
END;
$$ language 'plpgsql'
''',
'''CREATE OR REPLACE FUNCTION resultCache.expireQueriesTrigger() RETURNS trigger AS
$$
BEGIN
    PERFORM resultCache.expireQueries();
    RETURN OLD;
END;
$$ language 'plpgsql' ''',
'''CREATE TRIGGER expireTrigger AFTER INSERT OR UPDATE OR DELETE ON things
    EXECUTE PROCEDURE resultCache.expireQueriesTrigger()''')

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
