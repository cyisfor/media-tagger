from user import User
from orm import InnerJoin,OuterJoin,Select,AND,NOT,IN,array,AS,EQ,argbuilder,Type,Limit,Order,EXISTS
import db
import os

explain = 'explain' in os.environ
db.setup(source='sql/implications.sql')
db.setup(source='sql/searchcache.sql')

def decode_search(s):
	r = s[1:-1].decode().split(',')
	class SearchResult:
		table = r[0]
		count = int(r[1])
		def __repr__(self):
			return 'Search<'+self.table+','+str(self.count)+'>'
	return SearchResult()

db.registerDecoder(decode_search,'result','searchcache')

def combine(base,arg,op):
	if base is None:
		return arg
	return op(base,arg)

fullWhat = (
			'media.id',
			'media.name',
			'media.type',
			array(Select('tags.name',
						 InnerJoin('tags',AS(Select('unnest(neighbors)'),'neigh'),
								   EQ('neigh.unnest','tags.id'))))
			)



def assemble(tags,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
	arg = argbuilder()
	def prepareTags(ids):
		if not ids: return None
		res = [getTag(tag) if isinstance(tag,str) else tag for tag in tags.posi]
		res.sort()
		return res

	posi = prepareTags(tags.posi)
	nega = prepareTags(tags.nega)
	result = db.execute("SELECT searchcache.query($1::bigint[],$2::bigint[])",(posi,nega))[0][0]
	if User.noComics:
		where = NOT(IN('things.id',Select('medium','comicPage','which != 0')))
	else:
		where = None
	From = InnerJoin('things',result.table,EQ('things.id',result.table+'.id'))
	From = InnerJoin(From,'media',EQ('things.id','media.id'))
	mainCriteria = Select('things.id',From,where)
	mainOrdered = Limit(Order(mainCriteria,
	                          'media.added DESC'),
					(arg(offset) if offset else False),arg(limit))
	if wantRelated:
		mainOrdered = EQ('things.id',ANY(mainOrdered))
		if posi:
			# we want related tags, not literally the tags we're specifying
			mainOrdered = AND(
							NOT(EQ('tags.id',ANY(posi))),
				mainOrdered)
		# nearby tags to the results for our query...
		tagStuff = Select(
			['tags.id','first(tags.name) as name'],
			InnerJoin('tags','things',
					  EQ('tags.id','ANY(things.neighbors)')),
			mainOrdered)
		# limit results in a scope that the database can avoid calculating them all for 30s then throwing away 98% of them
		stmt = Select(['derp.id','derp.name'],
					  AS(
						  Limit(GroupBy(tagStuff,'tags.id'),
								limit=arg(taglimit)),
						  'derp'))
		# and order the tags by name, I guess.
		stmt = Order(stmt,'derp.name')
	else:
		# since we don't just need things.id, modify mainCriteria under mainOrdered's nose!
		mainCriteria.what = fullWhat
		if User.noComics:
			# we need a little extra info provided to show a glaringly obvious border
			mainCriteria.what += (
				EXISTS(Select(
					'medium','comicPage',EQ("things.id","comicPage.medium"))),)
		stmt = mainOrdered
	# we shouldn't ever need a with statement
	return stmt,arg,result.count


class CountedRange:
	"A range whose first element is the (finite) length of it."
	def __init__(self, iter):
		self.count = next(iter)
		self.__iter__ = iter
		
	    

def nabcount(f):
	def wrap(*a,**kw):
		iter = f(*a,**kw)
		return CountedRange(iter)

@nabcount
def searchForTags(tags,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
	stmt,args,count = assemble(tags,offset,limit,taglimit,wantRelated)
	stmt = stmt.sql()
	args = args.args
	if explain:
		print(stmt)
		print(args)
		stmt = "EXPLAIN ANALYZE "+stmt
	else:
		# yield count first of all
		yield count
	for row in db.execute(stmt,args):
		if explain:
			print(row[0])
			continue
		elif wantRelated:
			id,tag = row
			if isinstance(tag,str):
				yield tag
			else:
				# a tag with a NULL name snuck in there
				db.execute("DELETE FROM tags WHERE id = $1",(id,))
		else:
			yield row

def test():
	try:
		import tags
		from pprint import pprint
		bags = tags.parse("evil, red, -apple, -wagon")
		stmt,args,count = assemble(bags)
		print(count)
		print(stmt.sql())
		print(args.args)
		for thing in db.execute("EXPLAIN "+stmt.sql(),args.args):
			print(thing[0]);
		result = searchForTags(bags)
		print('count:', result.count)
		for id, in result:
			print('<a href="http://cy.h/art/~page/{:x}"><img src="http://cy.h/thumb/{:x}" /></a>'.format(id,id))
	except db.ProgrammingError as e:
		print(e.info['message'].decode('utf-8'))

if __name__ == '__main__':
	test()
