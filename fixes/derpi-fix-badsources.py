from favorites.parseBase import parse
import favorites.parsers
import db

def isgewd(uri):
    if not uri.startswith('https://derpibooru.org/'):
        return False
    for prefix in ('https://derpibooru.org/',
                   'https://derpibooru.org/images/'):
        try: int(uri[len(prefix):])
        except ValueError: pass
        else: return True
    return False

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
        for i,uri in enumerate(uris):
            if uri in baduris:
                for gooduri in uris:
                    if isgewd(gooduri):
                        parse(gooduri)
                        remove(image,sources[i])
                        print('got one',uri)
    input('ok?')
