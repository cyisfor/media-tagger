import versions,db
from tags import stmts

v = versions.Versioner('random')

# defaultTags means when there is no tags for a user, use the default ones as implied tags.
# defaultTags=False means when there are no tags, have no implied tags.

class VersionHolder:
    @v(version=1)
    def initially():
        db.setup('''CREATE TABLE randomSeen (
        id SERIAL PRIMARY KEY,
        media bigint UNIQUE REFERENCES things(id),
        category integer DEFAULT 0,
        UNIQUE(media,category))''')

v.setup()

def tagsfor(idents):
    print("\n".join(i[0] for i in db.c.execute('''EXPLAIN SELECT things.id,array(SELECT tags.name FROM tags INNER JOIN (SELECT unnest(neighbors)) AS neigh ON neigh.unnest = tags.id)
    FROM things WHERE things.id = ANY($1)''',(idents,))))
    raise SystemExit
    print('ident',idents)
    tags = [row for row in db.c.execute('SELECT things.id,array_agg(name) FROM tags INNER JOIN things ON ARRAY[tags.id] <@ things.neighbors WHERE ARRAY[things.id] <@ $1 GROUP BY things.id',(idents,))]
    print('tags',len(tags))
    return tags

def get(category=0,limit=0x30,where=None):
    stmt = stmts['positiveClause']
    stmt = stmt + " LEFT OUTER JOIN (SELECT media FROM randomSeen WHERE category = $1) AS randomSeen ON randomSeen.media = media.id"
    stmt = stmt + " WHERE"
    if where:
        stmt = stmt + " " + where + " AND"
    stmt = stmt + " randomSeen.media IS NULL"
    stmt = stmts['main'] % {
        'positiveClause': stmt,
        'negativeClause': '',
        'ordering': 'ORDER BY random() LIMIT $2'}
    print(stmt)
    rows = db.c.execute(stmt,(category,limit))
    #print('\n'.join(r[0] for r in rows))
    #raise SystemExit
    if rows:
        idents = [row[0] for row in rows]
        db.c.execute('INSERT INTO randomSeen (media,category) SELECT boop.unnest,$1 FROM randomSeen LEFT OUTER JOIN (SELECT unnest($2::bigint[])) AS boop ON randomSeen.media = boop.unnest WHERE randomSeen.id IS NULL',(category,idents))
    else:
        # out of images, better throw some back into the pot
        with db:
            db.c.execute('DELETE FROM randomSeen WHERE category = $1 AND id < (SELECT AVG(id) FROM randomSeen)',(category,))
            db.c.execute('UPDATE randomSeen SET id = id - (SELECT MIN(id) FROM randomSeen) WHERE category = $1',(category,))
            db.c.execute("SELECT setval('randomSeen_id_seq',(SELECT MAX(id) FROM randomSeen)")
        return get(category,limit,where)
    return rows

