import comic,db

comic = findComicByTitle("Anon's Pie Adventure", None)
def _(

which,medium = db.execute("SELECT which,medium FROM comic WHERE id = $1 ORDER BY medium DESC LIMIT 1")[0]

source = db.execute("SELECT uri FROM urisources WHERE id IN (select unnest(sources) FROM media WHERE id = $1) AND uri LIKE $2",
										(medium,'https://derpibooru.org/%'))
assert(len(source) == 1)
source = source[0]

comic = 
