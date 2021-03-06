import db
from versions import Versioner
import filedb
import note

from itertools import count
import sys,os

version = Versioner('delete')

@version(1)
def _():
	db.setup('''CREATE TABLE blacklist(
		id SERIAL PRIMARY KEY,
	  oldmedium INTEGER NOT NULL REFERENCES media(id),
		hash character varying(28) UNIQUE,
		reason TEXT)''',
			 '''CREATE TABLE dupes(
		id SERIAL PRIMARY KEY,
		medium INTEGER REFERENCES media(id),
		hash character varying(28) UNIQUE,
		inferior BOOLEAN DEFAULT FALSE,
		UNIQUE(medium,hash))''')

@version(2)
def _():
	# batch clearing of neighbors for deleting
	db.setup(
			'''CREATE TABLE IF NOT EXISTS doomed (
			id INTEGER PRIMARY KEY REFERENCES media(id) ON DELETE CASCADE)
			''',
			'''ALTER TABLE blacklist ADD COLUMN oldmedium INTEGER''',
			'''ALTER TABLE dupes ADD COLUMN oldmedium INTEGER''')

version.setup()
	
def start(s):
	sys.stdout.write(s+'...')
	sys.stdout.flush()

def done(s=None):
	if s is None: s = 'done.'
	print(s)


def commitDoomed():
	start("tediously clearing neighbors")
	# it's way less lag if we break this hella up
	with db.transaction():
		note("find things with doomed neighbors")
		db.execute("""
		CREATE TEMPORARY TABLE doomed_neighbors
ON COMMIT DROP
		AS
		SELECT id FROM things WHERE neighbors && array(SELECT id FROM doomed)""")
		note("remove doomed from neighbors")
		db.execute("""UPDATE things SET neighbors =
		array(SELECT unnest(neighbors) EXCEPT SELECT id FROM doomed)
		WHERE
		id IN (select id FROM doomed_neighbors)""")
		note("remove sources for doomed media")
		db.execute("""
		DELETE FROM sources
		USING media
		WHERE
		media.id in (select id from doomed)
		AND sources.id = ANY(media.sources)""")
		note("delete doomed media")
		db.execute("DELETE FROM things WHERE id in (select id from doomed)")
	done()

commitDoomed()

def justdelete(bad):
	db.execute('INSERT INTO doomed (id) SELECT id FROM media WHERE id = $1',(bad,))

def dbdelete(good,bad,reason,inferior):
	print("deleting {:x}".format(bad),'dupe' if good else reason)
	# the old LEFT OUTER JOIN trick to skip duplicate rows
	if good:
		# XXX: this is bad and I feel bad...
		db.execute("INSERT INTO dupes (oldmedium,medium,hash,inferior) SELECT $2, $1,media.hash,$3 from media LEFT OUTER JOIN blacklist ON media.hash = blacklist.hash where blacklist.id IS NULL AND media.id = $2",(good, bad, inferior))
	else:
		db.execute("INSERT INTO blacklist (oldmedium,hash,reason) SELECT $2,media.hash,$1 from media LEFT OUTER JOIN blacklist ON media.hash = blacklist.hash where blacklist.id IS NULL AND media.id = $2",(reason,bad))
	justdelete(bad)


def filedelete(bad):
	for category in ('media','thumb','resized'):
		place=os.path.join(filedb.top,category)
		doomed = os.path.join(place,'{:x}'.format(bad))
		# if we crash here, transaction will abort and the images will be un-deleted
		# but will get deleted next time so that the files are cleaned up
		if os.path.exists(doomed):
			os.unlink(doomed)

def dupe(good, bad, inferior=True):
	with db.transaction():
		dbdelete(good,bad,None,inferior)
		filedelete(bad)

def delete(bad, reason=None):
	print('deleting',bad,reason)
	with db.transaction():
		dbdelete(None, bad, reason, False)
		filedelete(bad)

def findId(uri):
	uri = uri.rstrip("\n/")
	uri = uri.rsplit('/')[-1].rstrip()
	return int(uri,0x10)

if __name__ == '__main__':
	def deleteordupe(bad, reasonorgood):
		if 'dupe' in os.environ:
			dupe(findId(reasonorgood),bad,'inferior' in os.environ)
		else:
			delete(bad, reasonorgood)
	if len(sys.argv)==3:
		deleteordupe(findId(sys.argv[1]),sys.argv[2])
	elif os.environ.get('stdin'):
		reason = sys.stdin.readline()
		for line in sys.stdin:
			deleteordupe(findId(line),reason)
	else:
		import gtkclipboardy as clipboardy
		reason = os.environ['reason']
		def gotPiece(piece):
			print('derp',piece)
			try:
				deleteordupe(findId(piece),reason)
			except ValueError: pass
		try: clipboardy(gotPiece).run()
		except KeyboardInterrupt: pass
	commitDoomed()
