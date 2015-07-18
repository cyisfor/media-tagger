from favorites.parseBase import parse
import favorites.parsers
import db

def remove(image,source):
    db.execute('''
UPDATE media SET sources = array(select unnest(sources) EXCEPT select $2) WHERE id = $1''',(image,source))

baduris = set((
 'https://derpibooru.org/submissionview.php',
 ))
    
with db.transaction():
    for image,uris,sources in db.execute('''
SELECT id,array(select uri from urisources where id in (select unnest(sources))),sources FROM media 
WHERE 
(
  id in (select id from things where neighbors && array(select id from tags where $1 @> ARRAY[name])) 
) AND 
sources && array(select id from urisources where $2 @> ARRAY[uri])
order by id desc limit 100
''',(('derpibooru','general:derpibooru'),tuple(baduris))):
        print(hex(image),uris)
        for uri in uris:
            if uri in baduris:
                parse(uri)
                remove(image,source)
                print('got one',uri)
    input('ok?')
