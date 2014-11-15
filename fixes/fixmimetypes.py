import db,create,filedb,derpmagic as magic

exceptionallyBadlyNamed = {
        0xf7a,
        0x145e,
        0x7518,
        0x61ba1,
        0x61ba2,
        0x61ba3,
        0x61bb9,
        0x61b9e,
        0x61b9d,
        0x61b9a
        }

with db.transaction():
    for image,name in db.c.execute('''SELECT media.id,media.name FROM media 
    INNER JOIN images ON media.id = images.id 
    WHERE 
    media.type = 'image/jpeg' AND NOT (
        media.name LIKE '%.jpg' OR
        media.name LIKE '%.jpeg' OR
        media.name LIKE '%.jpe' OR
        media.name LIKE '%.JPG' OR
        media.name LIKE '%.JPEG')
        '''):
        print(hex(image),name)
        if image in exceptionallyBadlyNamed:
            db.c.execute('UPDATE media SET name = $1 WHERE id = $2',(name.rsplit('.',1)[0]+'.jpg',image))
        elif name[-1] == '.':
            db.c.execute('UPDATE media SET name = name || $1 WHERE id = $2',('jpg',image))
        elif not '.' in name:
            db.c.execute('UPDATE media SET name = name || $1 WHERE id = $2',('.jpg',image))
        elif name.startswith('displayimage.php'):
            db.c.execute('UPDATE media SET name = $1 WHERE id = $2',('image.jpg',image))
        elif '?' in name:
            db.c.execute('UPDATE media SET name = $1 WHERE id = $2',(name.split('?')[0],image))
        else:
            source = filedb.mediaPath(image)
            info,type = create.openImage(source)
            if type == 'image/jpeg':
                print('WARNING BAD EXTENSION')
                db.c.execute('UPDATE media SET name = $1 WHERE id = $2',(name.rsplit('.',1)[0]+'.jpg',image))
            else:
                db.c.execute('UPDATE media SET type = $1 WHERE id = $2',(type,image))
            db.c.execute('COMMIT')
            db.c.execute('BEGIN')
