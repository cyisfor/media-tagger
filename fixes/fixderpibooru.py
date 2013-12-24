import db
import favorites.parsers
parse = favorites.parsers.parse.parse

booru = db.c.execute("SELECT id FROM tags WHERE name = $1",('derpibooru',))[0][0]

for medium,sources in db.c.execute("SELECT id,array(select uri from urisources where id = ANY(sources)) FROM media WHERE id IN (SELECT unnest(neighbors) FROM things WHERE id = $1) ORDER BY added DESC",(booru,)):
    hasIt = False
    main = None
    print(medium)
    for source in sources:
        print(source)
        if 'derpibooru' in source:
            main = source
    if main:
        parse(main)
