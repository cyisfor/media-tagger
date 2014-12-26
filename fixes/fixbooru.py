import db
import favorites.parsers
parse = favorites.parsers.parse.parse

booru = db.execute("SELECT id FROM tags WHERE name = $1",('booru:furry',))[0][0]

for medium,sources in db.execute("SELECT id,array(select uri from urisources where id = ANY(sources)) FROM media WHERE id IN (SELECT unnest(neighbors) FROM things WHERE id = $1) ORDER BY added DESC",(booru,)):
    hasIt = False
    main = None
    print(medium)
    for source in sources:
        print(source)
        if not 'booru' in source:
            hasIt = True
            break
        if 'index.php' in source:
            main = source
    if hasIt is False:
        assert(main is not None)
        parse(main)
