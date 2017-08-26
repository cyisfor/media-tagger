import db,sys

from versions import Versioner
version = Versioner('desc')
@version(1)
def _():
	db.execute('''CREATE TABLE descriptions (
id INTEGER PRIMARY KEY REFERENCES media(id) 
  ON DELETE CASCADE ON UPDATE CASCADE NOT NULL, 
blurb TEXT)''')
@version(2)
def _():
	db.setup('ALTER TABLE descriptions ADD COLUMN manual BOOLEAN DEFAULT FALSE NOT NULL',
					 'ALTER TABLE descriptions ADD COLUMN modified TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL')
	# or just add a column... meh

version.setup()

def describe(ident,manual=False):
	def changed(blurb=None):
		r = db.execute('SELECT id FROM descriptions WHERE id = $1',(ident,))
		if r:
			if blurb:
				db.execute('UPDATE descriptions SET blurb = $2, modified = now(), manual = $3 WHERE id= $1',
									 (ident,blurb,manual))
		else:
			r = db.execute('INSERT INTO descriptions (id,blurb,manual) VALUES ($1,$2,$3) RETURNING id',
										 (ident,blurb,manual))
			assert r
		db.execute('COMMIT')
		r = r[0][0]
		print('id',hex(r))
		return r
	def operation(change):
		blurb = db.execute("SELECT blurb FROM descriptions WHERE id = $1",
													(ident,))
		if blurb:
			blurb = blurb[0][0]
		db.execute('BEGIN')
		blurb = change(blurb,changed)
	return operation
