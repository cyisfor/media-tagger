import withtags,tags,db,user
import favorites.parse
import favorites.parsers

def setup():
	user.User.noComics = False

	withtags.tagsWhat = ["media.id"]
	images,args = withtags.tagStatement(tags.parse("comic:a dash of peppermint, comic:mommy issues"),limit=0x100)
	# With(body) > Limit(clause)
	sql = "CREATE TABLE IF NOT EXISTS need_retagging AS " + images.sql()
	db.execute(sql,args.args)

setup()

with db.transaction():
	db.execute("UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT id FROM need_retagging) WHERE id in (select id from things where neighbors && array(SELECT id FROM need_retagging) INTERSECT SELECT id FROM tags WHERE name LIKE 'comic:%')")
	print("boop")
	db.execute("UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT id FROM tags WHERE name LIKE 'comic:%') WHERE id IN (SELECT id FROM need_retagging)")
	for id, in db.execute("select id from need_retagging"):
		for source, in db.execute("SELECT urisources.uri FROM urisources inner join sources on sources.id = urisources.id WHERE uniquelyidentifies AND sources.id IN (SELECT unnest(sources) FROM media where id = $1)",(id,)):
			if source.startswith("https://derpicdn.net"): continue
			if source.startswith("https://static1.e621.net"): continue
			print("retagging",hex(id),source)
			try: favorites.parse.parse(source)
			except setupurllib.URLError as e:
				print(e.args[0])
				continue;
			except favorites.parse.ParseError as e:
				print(e)
				continue
			db.execute("DELETE FROM need_retagging WHERE id = $1",(id,))
			break
	db.execute("DROP TABLE need_retagging")
