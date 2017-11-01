from orm import Select,InnerJoin,AND,OR,With,EQ,NOT,Intersects,array,IN,Limit,Order,AS,EXISTS,Type,ANY,Func,Union,EVERY,GroupBy,argbuilder,Group
#ehhh
# TODO: declare a cursor, then FETCH to scroll around it, deleting when the query changes
# no LIMIT or OFFSET clauses
# one cursor per user...

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
		for ident,tag in tags:
			if isinstance(tag,'str'):
				yield tag
			else:
				db.execute("DELETE FROM tags WHERE id = $1",(ident,))
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


def tagStatement(tags,wantRelated=False,taglimit=0x30):
	From = InnerJoin('media','things',EQ('things.id','media.id'))
	negaWanted = Select('id','unwanted')
	negaClause = NOT(Intersects('neighbors',array(negaWanted)))
	if not (tags.posi or tags.nega):
		where = None
	elif tags.posi:
		where = Group(Select(EVERY(Intersects('neighbors','tags')),'wanted'))

		if tags.nega:
			negaWanted.where = NOT(IN('id',Select('unnest(tags)','wanted')))
			where = AND(where,negaClause)
	elif tags.nega:
		# only negative tags
		negaWanted.where = None
		where = negaClause

	if User.noComics:
		comic = Select("FIRST(comic)","comicPage",EQ("medium","things.id"))
		maxwhich = Select("MAX(which)","comicpage",EQ("comic",comic))
		not_last = Select("medium","comicpage",AND(EQ("comic",comic),NOT(EQ("which",maxwhich))))
		# if it's not in the list of not-last pages, then pick it.
		last_page = NOT(IN('things.id',not_last))
		if where is None:
			where = last_page
		else:
			where = AND(where,last_page)
	arg = argbuilder()

	mainCriteria = Select('things.id',From,where)
	mainOrdered = Order(mainCriteria,
						  'media.added DESC')
	mainOrdered.is_array = True
		
	if tags.posi:
		posi = Type(arg([getTag(tag) if isinstance(tag,str) else tag for tag in tags.posi]),'int[]',True)


	if wantRelated:
		mainOrdered = Group(Limit(mainOrdered,limit=arg(taglimit)))
		mainOrdered.is_array = True
		mainOrdered = EQ('things.id',ANY(mainOrdered))
		if tags.posi:
			mainOrdered = AND(
							NOT(EQ('tags.id',ANY(posi))),
				mainOrdered)

		tagStuff = Select(
			['tags.id','first(tags.name) as name'],
			InnerJoin('tags','things',
					  EQ('tags.id','ANY(things.neighbors)')),
			mainOrdered)
		lim = GroupBy(tagStuff,'tags.id')
#		if taglimit:
#			lim = Limit(lim,limit=arg(taglimit)),
		stmt = Select(['derp.id','derp.name'],AS(lim,'derp'))

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

	if tags.nega:
		nega = Type(arg([getTag(tag) if isinstance(tag,str) else tag for tag in tags.nega]),'int[]',True)
		notWanted = EQ('things.id',ANY(nega))
		if tags.posi:
			notWanted = AND(notWanted,
							NOT(EQ('things.id',ANY(posi))))
		herp = AS(Func('unnest',nega),'id')

		clauses['unwanted'] = (
			'id',
			Union(Select('tags.id',
						 InnerJoin('tags','things',
								   EQ('tags.id','things.id')),
									 notWanted),
				  Select('id',herp)))
	else:
		notWanted = None

	if tags.posi:
		# make sure positive tags don't override negative ones
		noOverride = NOT(EQ('things.id',ANY(posi)))
		notWanted = AND(notWanted,noOverride) if notWanted else noOverride
		# MUST separate implications to separate arrays
		# for the AND requirement a & b & c = (a|a2|a3)&(b|b2|b3)&...
		clauses['wanted'] = ('tags',Select(array(Select('implications(unnest)')),
										   Func('unnest',posi)))
												 


	#sel = stmt.clause.clause
	#sel.what = 'media.id, neighbors'
	#sel.where = Group(Select(EVERY(Intersects('neighbors','wanted.tags')),'wanted'))
	#stmt = 'SELECT tags FROM wanted WHERE $1::int > -1000'

	if clauses:
		stmt = With(stmt,**clauses)

	return stmt,arg

cursors = {}

def close_later(cursor):
	import gevent
	@gevent.spawn
	def squeak():
		gevent.sleep(10)
		cursor.close()

	return squeak

def addcursor(key,cursor):
	cursors[key] = cursor
	def poke():
		if cursor.timeout:
			cursor.timeout.kill()
		cursor.timeout = close_later(cursor)
		# the gevent SHOULD keep a ref until the timeout...
	cursor.poke = poke
	cursor.timeout = None
	cursor.poke()

from hashlib import sha1
from base64 import b64encode

def searchForTags(tags,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
	cursor = cursors.get((User.id,wantRelated))
	stmt,args = tagStatement(tags,wantRelated,taglimit)
	stmt = stmt.sql()
	args = args.args
	if cursor:
		if not cursor.same(stmt,args):
			cursor.timeout.kill()
			cursor.close()
			cursor = None
	else:
		cursor = None
	if cursor:
		cursor.poke()
	else:
		if explain:
			print(stmt)
			print(args)
			stmt = "EXPLAIN ANALYZE "+stmt

		name = "c"+str(str(User.id)+("t" if wantRelated else "f"))
		cursor = db.cursor(name,stmt,args)
		addcursor((User.id,wantRelated), cursor)

	cursor.move(offset)
	for row in cursor.fetch(limit):
		if explain:
			print(row[0])
		else:
			if wantRelated:
				ident,tag = row
				if isinstance(tag,str):
					yield tag
				else:
					# wat
					db.execute("DELETE FROM tags WHERE id = $1",(ident,))
					db.retransaction()
			else:
				yield row
	if explain:
		raise SystemExit

def test():
	try:
		import tags
		from pprint import pprint
		bags = os.environ.get('tags','evil, red, -apple, -explicit')
		bags = tags.parse(bags)
		stmt,args = tagStatement(bags)
		print(stmt.sql())
		print(args.args)
		for thing in db.execute("EXPLAIN ANALYZE DECLARE derp SCROLL CURSOR WITH HOLD FOR "+stmt.sql(),args.args):
			print(thing[0]);
		return
		for tag in searchForTags(bags):
			print(tag)
	except db.ProgrammingError as e:
		print(e.info['message'].decode('utf-8'))

if __name__ == '__main__':
	test()
