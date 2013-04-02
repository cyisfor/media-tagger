import db,sys

try:
    db.c.execute("""CREATE OR REPLACE FUNCTION clearneighbors() RETURNS trigger AS $$
    BEGIN
        UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT OLD.id) where neighbors @> ARRAY[OLD.id];
        RETURN OLD;
    END;
$$ LANGUAGE plpgsql""")

    db.c.execute("""CREATE TRIGGER emptythings BEFORE DELETE ON things
        FOR EACH ROW
        EXECUTE PROCEDURE clearneighbors()""")
except db.ProgrammingError: pass

def delete(thing):
    with db.transaction():
        db.c.execute("DELETE FROM things WHERE id IN (SELECT id FROM tags WHERE name = $1 or name = 'general:' || $1)",(thing,))
        print(thing)

if len(sys.argv)==2:
    delete(sys.argv[1])
else:
    for line in sys.stdin:
        delete(line.rstrip())
