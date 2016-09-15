from orm import InnerJoin,OuterJoin,Select

def search(tags):
	table = db.execute("searchcache.query($1::bigint[],$2::bigint[])",
	                   sorted(tags.posi),sorted(tags.nega))
	tags = Select('id',table);
	
