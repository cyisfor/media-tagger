from orm import InnerJoin,OuterJoin

def search(tags):
	tags.posi.sort()
	tags.nega.sort()
	table = db.execute("searchcache.search($1::bigint[],$2::bigint[])",
	                   sorted(tags.posi),sorted(tags.nega))
	return db.execute("SELECT id FROM " + table)
