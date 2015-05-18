from favorites.parseBase import parse
import favorites.parsers
import db

for image,sources in db.execute('SELECT id,array(select uri from urisources where id in (select unnest(sources))) FROM media WHERE array_length(sources,1) = 3 AND id in (select unnest(neighbors) from things where things.id = (select id from tags where name = $1) OR id in (select id from things where neighbors @> ARRAY[(select id from tags where name = $1)])) order by id desc limit 100',('derpibooru',)):
    print(hex(image))
    for source in sources:
        if source.startswith('https://derpibooru.org'):
            parse(source)
