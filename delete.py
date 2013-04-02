import db,sys

def delete(thing):
    with db.transaction():
        db.c.execute("UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT $1) where neighbors @> ARRAY[$1]",(thing,))
        db.c.execute("DELETE FROM things WHERE id = $1",(thing,))

if len(sys.argv)==2:
    delete(int(sys.argv[1],0x10))
else:
    for line in sys.stdin:
        delete(int(line.rsplit('/',1)[-1],0x10))
