import db,sys

from versions import Versioner
version = Versioner('desc')
@version(1)
def _():
    db.execute('''CREATE TABLE descriptions (
id bigint PRIMARY KEY REFERENCES media(id) 
  ON DELETE CASCADE ON UPDATE CASCADE NOT NULL, 
blurb TEXT)''')
    # or just add a column... meh

version.setup()

def main():
    ident = int(input('ID: '),0x10)
    blurb = sys.stdin.read().strip()
    db.execute('BEGIN')
    r = db.execute('SELECT id FROM descriptions WHERE id = $1',(ident,))
    if r:
        db.execute('UPDATE descriptions SET blurb = $1 WHERE id= $2',(blurb,ident))
    else:
        r = db.execute('INSERT INTO descriptions (blurb,id) VALUES ($1,$2) RETURNING id',
                   (blurb,ident))
    db.execute('COMMIT')
    print('id',hex(r[0][0]))

if __name__ == '__main__':
    main()
