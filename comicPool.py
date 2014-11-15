import setupurllib
import favorites.parseBase as parse
import favorites.parsers
import comic
import db

from bs4 import BeautifulSoup
import os
import urllib.parse

from itertools import count


#urllib.request.urlretrieve(base,'derp.html')

#db.c.execute('DROP FUNCTION setComicPage(INT,INT,INT)')
db.setup('''
CREATE OR REPLACE FUNCTION setComicPage(_image INT, _comic INT, _which INT) RETURNS VOID AS
$$
BEGIN
    LOOP
        -- first try to update the key
        UPDATE comicPage set image = _image where comic = _comic and which = _which;
        IF found THEN
            RETURN;
        END IF;
        -- not there, so try to insert the key
        -- if someone else inserts the same key concurrently,
        -- we could get a unique-key failure
        BEGIN
            INSERT INTO comicPage(image,comic,which) VALUES (_image,_comic,_which);
            RETURN;
        EXCEPTION WHEN unique_violation THEN
            -- Do nothing, and loop to try the UPDATE again.
        END;
    END LOOP;
END;
$$
LANGUAGE plpgsql''',
'''
CREATE OR REPLACE FUNCTION findURISource(_uri TEXT) RETURNS int AS
$$
DECLARE
_id int;
BEGIN
    LOOP
        -- first try to find it
        SELECT id INTO _id FROM urisources WHERE uri = _uri;
        IF found THEN
            return _id;
        END IF;
        BEGIN
            INSERT INTO sources DEFAULT VALUES RETURNING id INTO _id;
            INSERT INTO urisources (id,uri) VALUES (_id,_uri);
        EXCEPTION WHEN unique_violation THEN
            -- Do nothing we can just find it now.
        END;
    END LOOP;
END;
$$
LANGUAGE plpgsql''')

def isNext(s):
    s = s.lower()
    if s == '>>': return True
    if 'next' in s: return True

def getPool(base):
    print('base',base)
    whicher = count(0)
    title = None
    while True:    
        #with open('derp.html') as inp:
        with setupurllib.myopen(base) as inp:
            doc = BeautifulSoup(inp)

        if title is None:
            h4 = doc.find('h4')
            if not h4:
                print(doc)
                raise SystemExit
            title = h4.string.strip()
            print(title)

            def getinfo():
                description = h4.next_element.string.strip()
                if description: return description
                return input('Description: ').strip()

            com = comic.findComicByTitle(title,getinfo)
            source = db.c.execute("SELECT findURISource($1)",(base,))[0][0]
            db.c.execute("UPDATE comics SET source = $1 WHERE id = $2",(source,com))
            db.retransaction()
            print('updooted',com,source)

        #db.c.verbose = True
        for img in doc.findAll('img'):
            if not (img.has_attr('class') and 'preview' in img['class']): continue
            a = img.parent
            if (not a) or (a.name != 'a') or (not a.has_attr('href')): continue
            url = urllib.parse.urljoin(base,a['href'])
            url = parse.normalize(url)
            image = db.c.execute("SELECT media.id FROM media INNER JOIN sources ON media.sources @> ARRAY[sources.id] INNER JOIN urisources ON urisources.id = sources.id where urisources.uri = $1",(url,))
            if image:
                image = image[0][0]
            else:
                try: 
                    image = parse.parse(url)
                except parse.ParseError: continue
                db.retransaction()                
            which = next(whicher)
            for tries in range(2):
                try: db.c.execute('SELECT setComicPage($1,$2,$3)',(image,com,which))
                except db.ProgrammingError as original:
                    db.retransaction(rollback=True)
                    import create
                    try: create.retryCreateImage(image)
                    except db.ProgrammingError:
                        # giving up
                        raise original
        nextbase = doc.find(lambda tag: tag.name == 'a' and tag.string and isNext(tag.string.strip()))
        if not nextbase: break
        nextbase = nextbase['href']
        if not nextbase: break
        print('next',nextbase)
        base = urllib.parse.urljoin(base,nextbase)

if __name__ == '__main__':
    if 'stdin' in os.environ:
        import sys
        for line in sys.stdin:
            getPool(line)
    else:
        getPool(os.environ['url'])
