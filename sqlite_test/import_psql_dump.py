import sys,sqlite3

findMedia,media,findTags,tags,findConns,connections = range(6)

derp = sqlite3.connect("pics.sqlite")
db = derp.cursor()

with open('schema.sql',encoding='utf-8') as inp:
    try: db.executescript(inp.read())
    except sqlite3.OperationalError: pass

derp.commit()
db = derp.cursor()
    
mode = findMedia

for i,line in enumerate(sys.stdin):
    if i % 0x1000 == 0:
        print('commit')
        derp.commit()
        db = derp.cursor()
    if mode == findMedia:
        if line.startswith('----'): mode = media
    elif mode == findTags:
        if line.startswith('----'): mode = tags
    elif mode == findConns:
        if line.startswith('----'): mode = connections    
    elif mode == media:
        if line[0] == '(':
            mode = findTags
            continue
        fields = ('id','name','created','hash','added','size','type','md5','thumbnailed','modified','phashfail','phash')
        record = [s.strip() for s in line.split(' | ')]
        record[9:] = record[10:] # sources
        
        db.execute("INSERT INTO media (" + ', '.join(fields) + ") VALUES ("+', '.join('?' for f in fields)+")",record)
    elif mode == tags:
        if line[0] == '(':
            mode = findConns
            continue
        id, name = [s.strip() for s in line.split(' | ')]
        if not name: continue
        print('?',id,name)
        try: db.execute("INSERT OR REPLACE INTO tags (id,name) VALUES (?,?)",(id,name))
        except sqlite3.IntegrityError:
            print('tag',name,'failed')
            raise
    elif mode == connections:
        if line[0] == '(':
            break
        media, tag = [s.strip() for s in line.split(' | ')]
        db.execute("INSERT OR REPLACE INTO media_tags (medium,tag) VALUES(?,?)",(media,tag))
