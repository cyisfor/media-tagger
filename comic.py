import note
from versions import Versioner
from db import vsetup,transaction
import db
from redirect import Redirect

from setupurllib import urlerror
Error = urlerror.HTTPError
from functools import wraps

version = Versioner('comic')

@version(1)
def go():
	vsetup("""CREATE TABLE comics
	(id INTEGER PRIMARY KEY, 
	 title TEXT UNIQUE, 
	 description TEXT,
	 added TIMESTAMPTZ DEFAULT NOW())""",
	"""CREATE TABLE comicPage (id SERIAL PRIMARY KEY, 
		comic INTEGER REFERENCES comics(id) ON DELETE CASCADE ON UPDATE CASCADE,
		which INTEGER,
		medium INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE)""",
		"CREATE UNIQUE INDEX unique_pages ON comicPage(comic,which)",
		"""CREATE OR REPLACE FUNCTION setcomicpage(_medium integer, _comic integer, _which integer) RETURNS void AS
$$

BEGIN												  
	 LOOP											   
		 -- first try to update the key 
		 UPDATE comicPage set medium = _medium where comic = _comic and which = _which;
		 IF found THEN								  
			 RETURN;									
		 END IF;										
		 -- not there, so try to insert the key		 
		 -- if someone else inserts the same key concurrently
		 -- we could get a unique-key failure		   
		 BEGIN										  
			 INSERT INTO comicPage(medium,comic,which) VALUES (_medium,_comic,_which);
			 RETURN;									
		 EXCEPTION WHEN unique_violation THEN		   
			 -- Do nothing, and loop to try the UPDATE again.
		 END;										   
	 END LOOP;										  
END;
$$ language 'plpgsql'""")

@version(2)
def go():
	vsetup("ALTER TABLE comics ADD COLUMN tags INTEGER[]")

version.setup()
	
def withC(f):
	@wraps(f)
	def wrapper(*a,**kw):
		with transaction():
			f(*a,**kw)
	return wrapper

def findWhich(com, which):
	res = db.execute("SELECT (MAX(which) + $2) % MAX(which) FROM comicPage WHERE comic = $1",
									 (com,which))
	return res[0][0]

def findComicByTitle(title,getinfo=None):
	rows = db.execute("SELECT id FROM comics WHERE title = $1",(title,));
	if len(rows) == 0:
		print("Couldn't find title",title)
		assert(getinfo is not None)
		@getinfo
		def handle(description):
			nonlocal rows
			with db.transaction():
				rows = db.execute("SELECT id FROM comics WHERE title = $1",
				(title,))
				if rows:
					# nehh, race condition, something else created this comic!
					return rows[0][0]
				try:
					rows = db.execute("INSERT INTO comics (title,description) VALUES ($1,$2) RETURNING id",
														(title,
														 description))
				except db.ProgrammingError:
					db.retransaction(rollback=True)
					# the counter doesn't get auto-incremented when we specify the comic ID ourselves
					db.execute("SELECT setval('comics_id_seq'::regclass,MAX(id),true) FROM comics")
					rows = db.execute("INSERT INTO comics (title,description) VALUES ($1,$2) RETURNING id",
														(title,
														 description))
										 
	return rows[0][0]

def findInfoDerp(id):
	return db.execute("SELECT title,description,(SELECT uri FROM urisources WHERE id = comics.source),array(SELECT name from tags WHERE comics.tags @> ARRAY[id]) FROM comics WHERE id = $1",(id,))

def findInfo(id,getinfo,next):
	rows = findInfoDerp(id)
	if len(rows) == 0:
		print('comic',hex(id),'no exist')
		@getinfo
		def result(title, description, source, tags):
			with db.transaction():
				db.execute("INSERT INTO comics (id,title,description) VALUES ($1,$2,$3) RETURNING id",(id,title,description))
			if next: return next(title,description,source,tags)
		return result
	elif next:
		return next(*rows[0])

def findMediumDerp(comic,which,medium=None):
	rows = db.execute("SELECT medium FROM comicPage WHERE comic = $1 AND which = $2",(comic,which))
	if len(rows)==0:
		if medium:
			with db.transaction():
				db.execute("INSERT INTO comicPage (comic,which,medium) VALUES ($1,$2,$3)",(comic,which,medium))
				db.execute("UPDATE comics SET added = now() WHERE id = $1",(comic,))
			return medium,True
		return None,False
	#note.yellow('medium existed',rows,medium)
	return rows[0][0],False

def findMedium(comic,which,medium=None):
	if medium:
		medium,created = findMediumDerp(comic,which,medium)
		return medium 
	for tries in range(2):
		medium,created = findMediumDerp(comic,which)
		if medium:
			return medium
		else:
			note.yellow('No medium for ',comic,which)
			np = pages(comic)
			if which == 0 and np == 0:
				return 0x5c911
			if which >= np:
				print('wnpt',which,np)
				# XXX: this should be in pages.py
				if which == 0:
					raise Redirect("../")
				raise Redirect("../0/")
			print("Time to reorder!")
			with db.transaction():
				db.execute("CREATE TEMPORARY TABLE orderincomix AS SELECT id,(row_number() OVER (partition by comic order by which))-1 AS which FROM comicpage")
				db.execute("UPDATE comicpage SET which = orderincomix.which FROM orderincomix WHERE orderincomix.id = comicpage.id")
				db.execute("DROP TABLE orderincomix")
	raise Error("I give up. The comic {:x} is messed up on page {:x}!".format(com,which))

def numComics():
	rows = db.execute("SELECT COUNT(id) FROM comics")
	return rows[0][0]

def pages(comic):
	rows = db.execute("SELECT COUNT(id) FROM comicPage WHERE comic = $1",(comic,))
	return rows[0][0]

def list(page,negatags=()):
	return db.execute("SELECT id,title,tags,array(select name from tags where id IN (SELECT unnest(comics.tags))) FROM comics WHERE array_length($1::INTEGER[],1) IS NULL OR tags IS NULL OR NOT tags && $1::INTEGER[] ORDER BY added DESC, id OFFSET $2 LIMIT $3",(tuple(negatags),page*0x20,0x20))

def tag(comic,tags):
	with db.transaction():
		db.execute('UPDATE comics SET tags = array(select unnest(tags) UNION select unnest($1::INTEGER[]) EXCEPT select unnest($2::INTEGER[])) WHERE id = $3',(tags.posi,tags.nega,comic))
