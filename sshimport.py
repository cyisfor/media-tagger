#!/usr/bin/python3

from favorites.things import Tag

import filedb
import shutil
import sys,os,tempfile

def main():
    for n in os.environ.keys():
        print(n)
    idnum = False
    with tempfile.NamedTemporaryFile(dir=os.path.join(filedb.base,'temp')) as temp:
        shutil.copyfileobj(sys.stdin,temp)
        sys.stdin.close()
        temp.seek(0,0)
        tags = [tag.strip() for tag in os.environ['tags'].split(',')]
        tags = [(Tag(*tag.split(':')) if ':' in tag else tag) for tag in tags]
        sourceURI = os.environ.get('source')
        hash = create.mediaHash(temp)
        idnum =  db.c.execute("SELECT id FROM media WHERE hash = $1",(hash,))
        if idnum:
            print("Existing medium found. Updating...")
        create.internet(copyMe(temp.name),None,tags,sourceURI,())
        try: temp.close()
        except OSError: pass
    if idnum:
        print("Medium updated!")
    else:
        print("Media added to gallery!")

if __name__ == '__main__': main()
