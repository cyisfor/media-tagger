from orm import Select,InnerJoin,AND,OR,With,EQ,NOT,Intersects,array,IN,Limit,Order,AS,EXISTS,Type,ANY,Func,Union,EVERY,GroupBy,argbuilder,Group,Contains
#ehhh

from user import User
import db												#
from versions import Versioner
import resultCache
from itertools import count
from tags import Taglist

import os

explain = 'explain' in os.environ

stmts = {}
import sqlparse
sqlparse.debugging = True
stmts = db.source('sql/withtags.sql')
db.setup(*db.source('sql/connect.sql',False))
db.setup(source='sql/implications.sql')
def derp():
	print('-'*60)
	for stmt in stmts.items():
		print(stmt)
		print('-'*60)
	raise SystemExit
#derp()

v = Versioner('tag')
@v(1)
def setup():
	db.execute(stmts['complextagalter'])
	db.execute(stmts['complextagindex'])
#db.execute(stmts['implications'])
class scalartuple(tuple):
	def __add__(self,other):
		if not isinstance(other,tuple):
			other = (other,)
		return scalartuple(super(scalartuple,self).__add__(other))

def nonumbers(f):
	def filter(tags):
		for id,tag in tags:
			if isinstance(tag,'str'):
				yield tag
			else:
				db.execute("DELETE FROM tags WHERE id = $1",(id,))
	def wrapper(*k,**a):
		return filter(f(*k,**a))
	return wrapper

tagsWhat = (
			'media.id',
			'media.name',
			'media.type',
			array(Select('tags.name',
						 InnerJoin('tags',AS(Select('unnest(neighbors)'),'neigh'),
								   EQ('neigh.unnest','tags.id'))))
			)

def lookup_tags(l):
	for i,tag in enumerate(l):
		if isinstance(tag,str):
			l[i] = getTag(tag)

def tagStatement(tags,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
	arg = argbuilder()

	notWanted = None
	if tags.nega:
		lookup_tags(tags.nega)
		if len(tags.nega) == 1:
			tag = tuple(tags.nega)[0]
			if not tag in tags.posi:
				notWanted = Type(arg(tag),'INTEGER')
		else:
			diff = tags.nega - tags.posi
			if len(diff) == 1:
				notWanted = Type(arg(tuple(diff)[0]),'INTEGER')
			elif diff:
				notWanted = Type(arg(diff),'INTEGER[]',array=True)
	From = InnerJoin('media','things',EQ('things.id','media.id'))
	if tags.nega:
		if len(tags.nega) == 1:
			negaClause = NOT(Contains('neighbors',notWanted))
		else:
			negaClause = NOT(Intersects('neighbors',notWanted))
	if not (tags.posi or tags.nega):
		where = None
	elif tags.posi:
		where = Group(Select(EVERY(Intersects('neighbors','tags')),'wanted'))

		if tags.nega:
			where = AND(where,negaClause)
	elif tags.nega:
		# only negative tags
		where = negaClause

	if User.noComics:
		first_page = NOT(IN('things.id',Select('medium','comicPage','which != 0')))
		if where is None:
			where = first_page
		else:
			where = AND(where,first_page)

	mainCriteria = Select('things.id',From,where)
	mainOrdered = Limit(Order(mainCriteria,
						  'media.added DESC'),
					(arg(offset) if offset else False),arg(limit))

	if tags.posi:
		lookup_tags(tags.posi)
		if len(tags.posi) == 1:
			posi = Type(arg(tuple(tags.posi)[0]),'INTEGER')
		else:
			posi = Type(arg([tags.posi]),'INTEGER[]',array=True)


	if wantRelated:
		mainOrdered = IN('things.id',mainOrdered)
		if tags.posi:
			mainOrdered = AND(
							NOT(EQ('tags.id',ANY(posi))),
				mainOrdered)

		tagStuff = Select(
			['tags.id','first(tags.name) as name'],
			InnerJoin('tags','things',
					  EQ('tags.id','ANY(things.neighbors)')),
			mainOrdered)
		stmt = Select(['derp.id','derp.name'],
					  AS(
						  Limit(GroupBy(tagStuff,'tags.id'),
								limit=arg(taglimit)),
						  'derp'))

		stmt = Order(stmt,'derp.name')
	else:
		mainCriteria.what = tagsWhat
		if User.noComics:

			mainCriteria.what += (
				EXISTS(Select(
					'medium','comicPage',EQ("things.id","comicPage.medium"))),)
		stmt = mainOrdered

	# we MIGHT need a with statement...
	clauses = {}

	if tags.posi:
		# MUST separate implications to separate arrays
		# for the AND requirement a & b & c = (a|a2|a3)&(b|b2|b3)&...
		if len(tags.posi) == 1:
			wanted = Select(AS(array(Select(Func('implications',posi))),"tags"))
		else:
			wanted = Select(AS(array(Select('implications(unnest)')),"tags"),
										   Func('unnest',posi))
		# make sure positive tags don't override negative ones
		if notWanted:
			if notWanted.is_array:
				derp = Intersects('tags',notWanted)
			else:
				derp = Contains('tags',notWanted)
			wanted = Select("tags",AS(wanted,"derp"),NOT(derp))
		clauses['wanted'] = ('tags',wanted)

	#sel = stmt.clause.clause
	#sel.what = 'media.id, neighbors'
	#sel.where = Group(Select(EVERY(Intersects('neighbors','wanted.tags')),'wanted'))
	#stmt = 'SELECT tags FROM wanted WHERE $1::int > -1000'

	if clauses:
		stmt = With(stmt,**clauses)

	return stmt,arg

def searchForTags(tags,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
	stmt,args = tagStatement(tags,offset,limit,taglimit,wantRelated)
	stmt = stmt.sql()
	args = args.args
	if explain:
		print(stmt)
		print(args)
		stmt = "EXPLAIN ANALYZE "+stmt
	for row in resultCache.encache(stmt,args,not explain):
		if explain:
			print(row[0])
		else:
			if wantRelated:
				id,tag = row
				if isinstance(tag,str):
					yield tag
				else:
					db.execute("DELETE FROM tags WHERE id = $1",(id,))
			else:
				yield row
	if explain:
		raise SystemExit


def test():
	try:
		import tags
		from pprint import pprint
		bags = os.environ.get('tags','evil, red, -apple, -wagon')
		bags = tags.parse(bags)
		stmt,args = tagStatement(bags)
		print(stmt.sql())
		print(args.args)
		for thing in db.execute("EXPLAIN ANALYZE "+stmt.sql(),args.args):
			print(thing[0]);
		return
		for tag in searchForTags(bags):
			print(tag)
	except db.ProgrammingError as e:
		print(e.info['message'].decode('utf-8'))

if __name__ == '__main__':
	test()
