import os,sys,io,shutil
import subprocess
import schema
import logging


logging.basicConfig(filename="debug.log",level=logging.INFO)
def mysteriousBugCopyHack(stmt,source):
    pid = subprocess.Popen(["psql","-p","5433","-U","ion","derp"],stdin=subprocess.PIPE)
    #pid = subprocess.Popen(["cat"],stdin=subprocess.PIPE,stdout=open("argh.dat","w"))
    pid.stdin.write((stmt+";\n").encode())
    shutil.copyfileobj(source,pid.stdin)
    pid.stdin.write("\\.\n".encode())
    pid.stdin.close()
    assert 0 == pid.wait()

def puller():
    sys.stdout = sys.stdout.detach() # send as binary (pg already makes utf-8)
    delimiter = "\\.\n".encode()
    from olddb import cursor
    with cursor() as c:
        logging.info("sending image")
        c.copy_expert("COPY image (id) TO STDOUT",sys.stdout)
        sys.stdout.write(delimiter)
        logging.info("sending tag")
        c.copy_expert("COPY tag (id) TO STDOUT",sys.stdout)
        sys.stdout.write(delimiter)
        logging.info("sending image_tag")
        c.copy_expert("COPY image_tag (image,tag) TO STDOUT",sys.stdout)
        sys.stdout.write(delimiter)
        logging.info("sending image w/ media and image info")
        c.copy_expert("COPY image (id,name,hash,created,added,size,type,md5,thumbnailed,animated,width,height,ratio) TO STDOUT",sys.stdout)
        sys.stdout.write(delimiter)
        logging.info("sending tag info")
        c.copy_expert("COPY tag (id,name) TO STDOUT",sys.stdout)
        sys.stdout.write(delimiter)
        logging.info("sending sources")
        c.copy_expert("COPY source (id,image,uri,code,checked) TO STDOUT",sys.stdout)
        logging.info("BOOP")
        sys.stdout.write(delimiter)
        c.copy_expert("COPY filesource (id,path) TO STDOUT",sys.stdout)
        sys.stdout.write(delimiter)
        sys.stdout.flush()

def pusher(source):
    stmts = []
            #images
    stmts.append("COPY things (id) FROM STDIN")
    stmts.append("CREATE TEMPORARY TABLE temptags (id integer)")
    stmts.append("COPY temptags (id) FROM STDIN")
    stmts.append("INSERT INTO things (id) SELECT (select MAX(id) FROM things)+id FROM temptags")
        logging.info("Got tag things, now imagetags")
        with temporaryTable(c,'image INTEGER, tag INTEGER') as table:
            c.copy_expert("COPY "+table+" FROM STDIN",source)
            c.execute("UPDATE things SET neighbors = derp.tag FROM (SELECT array_agg(tag) AS tag,image FROM "+table+" GROUP BY image) AS derp WHERE things.id = derp.image")
        logging.info("Got imagetags, now media")
        with temporaryTable(c,'id integer, name text, hash character varying(28), created timestamp with time zone, added timestamp with time zone, size integer, type text, md5 character(32), thumbnailed timestamp with time zone, animated boolean, width integer, height integer, ratio real') as table:
            c.copy_expert("COPY "+table+" FROM STDIN",source)
            c.execute("INSERT INTO media (id,name,hash,created,added,size,type,md5,thumbnailed) SELECT id,name,hash,created,added,size,type,md5,thumbnailed FROM "+table)
            logging.info("Got media, now image info")
            c.execute("INSERT INTO images (id,animated,width,height,ratio)  SELECT id,animated,width,height,ratio FROM "+table)
        c.execute("COMMIT")
        c.execute("BEGIN")
        logging.info("Got image info, now tag info")
        with temporaryTable(c,"id integer, name text") as table:
            c.copy_expert("COPY "+table+" FROM STDIN",source)
            c.execute("INSERT INTO tags (id,name) SELECT id+%s,name FROM "+table,
                    (maxthings,))
        logging.info("Got tag info, now uri sources")
        raise RuntimeError("This is horribly broken. Inserts X000 in the middle of my copy! THen trying to run it with psql separately kills my connection!")
        if derpyderp:
            with temporaryTable(c,'id integer, image integer, uri text, code integer, checked INTEGER',notSoTemp=True) as table:
                c.copy_expert("COPY "+table+" FROM STDIN",source)
                # two different images with the same source...
                c.execute("UPDATE "+table+" SET id = derp.derp FROM (SELECT id,min(id) over (partition by uri) as derp from "+table+") as derp where derp.id = "+table+".id")
                logging.info("Got uri sources, now set media sources")
                with temporaryTable(c,'id integer, path text',notSoTemp=True) as table2:
                    c.execute("COMMIT")
                    mysteriousBugCopyHack("COPY "+table2+" (id,path) FROM STDIN",source)
                    raise SystemExit
        # XXX: urgggh
        table = "temptable1"
        table2 = "temptable2"
        logging.info("YAY")
        c.execute("UPDATE "+table+" SET id = id - (SELECT min(id) FROM "+table+") + 1")
        c.execute("UPDATE "+table2+" SET id = id + (SELECT max(id) FROM "+table+") - (SELECT min(id) FROM "+table2+") + 1")
        c.execute("""UPDATE media SET sources = sauce FROM (
    SELECT array_agg(id) AS sauce,image FROM """+table+""" GROUP BY image
    UNION
    SELECT array_agg(id) AS sauce,id FROM """+table2+""" GROUP BY id
    ) AS derp WHERE derp.image = media.id""")
        logging.info("Set media sources, now file sources")
        c.execute("INSERT INTO sources (id) SELECT id FROM "+table2)
        c.execute("INSERT INTO filesources (id,path) SELECT id,path FROM "+table2)

        logging.info("Got file sources, now uri sources")
        c.execute("DELETE FROM "+table+" WHERE id NOT IN (SELECT DISTINCT id FROM "+table+")")
        c.execute("INSERT INTO sources (id,checked) SELECT id,TIMESTAMP WITH TIME ZONE 'epoch' + checked / 1000 * INTERVAL '1 second' FROM "+table)
        c.execute("INSERT INTO urisources (id,uri,code) SELECT DISTINCT id,uri,code FROM "+table)

        c.execute("DROP TABLE temptable1")
        c.execute("DROP TABLE temptable2")

        logging.info("uri sources set! Cleaning up sequence counters")
        for table in ('things','sources'):
           c.execute("SELECT setval('"+table+"_id_seq',MAX(id)) FROM "+table)
        logging.info("Cleaned up! Time to commit...")

r,w = os.pipe()
pid = os.fork()

if pid == 0:
    logging.info("Puller robot is go")
    os.dup2(w,sys.stdout.fileno())
    os.close(w)
    os.close(r)
    puller()
    logging.info("Get me outta here!")
    sys.stdout.close()
else:
    logging.info("Pusher robot is go")
    os.close(w)
    #shutil.copyfileobj(os.fdopen(r,mode="rb"),sys.stdout.detach())
    #raise SystemExit
    source = DelimitedFile(os.fdopen(r,mode="rb"))
    pusher(source)
    sys.stdin.close()
    os.waitpid(pid,0)
