import tags

from contextlib import contextmanager
from functools import reduce

import versions,db
from context import contextify

v = versions.Versioner('user')

# defaultTags means when there is no tags for a user, use the default ones as implied tags.
# defaultTags=False means when there are no tags, have no implied tags.

class VersionHolder:
	@v(version=1)
	def initially():
		db.setup("CREATE TABLE uzers (id SERIAL PRIMARY KEY, ident TEXT UNIQUE, rescaleImages boolean DEFAULT TRUE, defaultTags boolean DEFAULT TRUE)")
	@v(version=2)
	def impliedList():
		db.setup("CREATE TABLE uzerTags (id INTEGER REFERENCES tags(id),uzer INTEGER REFERENCES uzers(id), nega BOOLEAN DEFAULT FALSE)");
	@v(version=3)
	def sameTags():
		"Two users might want to have the same tag, one nega and one posi!"
		db.setup("CREATE TABLE uzerTags2 (id SERIAL PRIMARY KEY, tag INTEGER REFERENCES tags(id),uzer INTEGER REFERENCES uzers(id), nega BOOLEAN DEFAULT FALSE)",
			"INSERT INTO uzerTags2 (tag,uzer,nega) SELECT id,uzer,nega FROM uzerTags",
			"DROP TABLE uzerTags",
			"ALTER TABLE uzerTags2 RENAME TO uzerTags",
			"CREATE UNIQUE INDEX nodupeuzertags ON uzerTags(tag,uzer)")
	@v(version=4)
	def noComics():
		"Users might not want to see spammy comics in the listing?"
		db.setup("ALTER TABLE uzers ADD COLUMN noComics BOOLEAN NOT NULL DEFAULT TRUE");
	@v(version=5)
	def jsnavigate():
		"Users might want to navigate prev/next just by hitting left and right."
		db.setup("ALTER TABLE uzers ADD COLUMN navigate BOOLEAN NOT NULL DEFAULT FALSE")
	@v(version=6)
	def jsreload():
		"Users might be able to load individual failed thumbs, instead of the whole page"
		db.setup("ALTER TABLE uzers ADD COLUMN loadjs BOOLEAN NOT NULL DEFAULT FALSE")
v.setup()

def currentUser():
	return User

defaultTags = '-rating:explicit, -gore, -foalcon, -loli, -pedo'
dtags = tags.parse(defaultTags)

@contextify
class User:
	ident = None
	id = None
	rescaleImages = False
	defaultTags = None
	noComics = True
	navigate = False
	loadjs = False
	def tags():
		if User.defaultTags:
			return dtags
		result = tags.Taglist()
		for id,nega in db.execute("SELECT tag,nega FROM uzertags WHERE uzer = $1",(User.id,)):
			if nega:
				result.nega.add(id)
			else:
				result.posi.add(id)
		return result
	def visit(media):
		db.execute('SELECT uzerVisitsInsert($1,$2)',User.id,media)
	def __str__():
		return User.ident
	def __repr__():
		return '<user '+User.ident+'>'
	def setup(ident):
		for go in range(2):
			result = db.execute("SELECT id,rescaleImages,defaultTags,noComics,navigate,loadjs FROM uzers WHERE ident = $1",(ident,))
			if result and len(result[0]) == 6:
				result = result[0]
				User.ident = ident
				User.id = result[0]
				User.rescaleImages = result[1]
				User.defaultTags = result[2]
				User.noComics = result[3]
				User.navigate = result[4]
				User.loadjs = result[5]
				return
			db.execute("INSERT INTO uzers (ident) VALUES ($1)",(ident,))
		raise RuntimeError("Something's inserting the same user weirdly so the database is failing to get it at any time!")

being = User

def set(news):
	news = tuple(news)
	names = tuple(new[0] for new in news)
	values = tuple(new[1] for new in news)
	names = tuple("{} = ${}".format(name,i+1) for i,name in enumerate(names))
	stmt = "UPDATE uzers SET "+", ".join(names) + " WHERE id = ${}".format(len(names)+1)
	with db.transaction():
		db.execute(stmt,values+(User.id,))

class UserError(Exception): 
	def __init__(self,message,*args):
		self.message = message
		super().__init__((message,)+args)

