import versions,db
import withtags,tags as tagsModule
import eventlet

from orm import IS,EQ,Select,OuterJoin,AND,AS,argbuilder,InnerJoin,Limit,Order,With,NOT

import random

v = versions.Versioner('random')

@v(version=1)
def initially():
	db.setup('''CREATE TABLE randomSeen (
	id SERIAL PRIMARY KEY,
	media INTEGER NOT NULL REFERENCES things(id) ON DELETE CASCADE,
	category integer NOT NULL DEFAULT 0,
	UNIQUE(media,category))''')

@v(version=2)
def _():
	db.setup('ALTER TABLE randomSeen ADD COLUMN seen BOOLEAN NOT NULL DEFAULT FALSE',
					 'UPDATE randomSeen SET seen = TRUE',
					 'CREATE INDEX haveSeenRandom ON randomSeen(seen,category)')

	
v.setup()

def churn(category,tags,limit=9):
	print("churning...")

	stmt,arg = withtags.tagStatement(tags,limit=limit)
	cat = arg(category)
	# [with.base] -> limit.clause -> order.clause -> select
	base = stmt.body if hasattr(stmt,'body') else stmt
	base = base.clause # order (.clause -> select)
	notSeen = IS('randomSeen.media','NULL')
	base.clause.where = AND(base.clause.where,notSeen) if base.clause.where else notSeen
	base.clause.From = OuterJoin(base.clause.From,
								 AS(Select('media','randomSeen',
																				 EQ('category',cat)),
									'randomSeen'),
							EQ('randomSeen.media','media.id'))
	base.clause.what = ('media.id',cat)
	base.order = 'random(),'+arg(random.random())
	stmt = With(
		Select('count(*)','rows'),
		rows=(None,'INSERT INTO randomSeen (media, category) ' + stmt.sql() + '\nRETURNING 1')).sql()
	args = arg.args
	#print(stmt.replace('  ','.'))
	#print(args)
	#raise SystemExit

	while True:
		try:
			num = db.execute(stmt,args)[0][0]
		except db.ProgrammingError as e:
			derp = 0
			lines = stmt.split('\n')
			import math
			wid = int(1+math.log(len(lines)) / math.log(10))
			wid = '{:'+str(wid)+'}'
			def num():
				nonlocal derp
				ret = wid.format(derp)+' '
				derp += 1
				return ret
			print('\n'.join(num()+line for line in lines))
			print(e.info['message'].decode('utf-8'))
			raise SystemExit
		if num > 0: break
		# out of media, better throw some back into the pot
		with db.transaction():
			db.execute('DELETE FROM randomSeen WHERE category = $1 AND id < (SELECT AVG(id) FROM randomSeen WHERE category = $1)',(category,))
			# this shouldn't violate unique, since more than 1/2 were deleted
			# or... should it be SELECT MEDIAN(id) or something above?
			db.execute('UPDATE randomSeen SET id = id - (SELECT MIN(id) FROM randomSeen WHERE category = $1) WHERE category = $1',(category,))
			db.execute("SELECT setval('randomSeen_id_seq',(SELECT MAX(id) FROM randomSeen WHERE category = $1))",(category,))

def pickone(category, tags):
	if Session.prefetching: return

	unseen = db.execute("SELECT COUNT(1) FROM randomSeen WHERE category = $1 AND NOT seen",(category,))[0][0]
	print("unseen",unseen)
	if unseen == 0:
		# need some right away
		churn(category,tags,9)
	elif unseen < 9:
		@eventlet.spawn_n
		def churnLater():
			eventlet.sleep(0.1)
			churn(category,tags,9)
		print("churning later...",churnLater)

	#pick one... with the lowest id but not seen
	db.execute("UPDATE randomSeen SET seen = TRUE WHERE id IN (SELECT id FROM randomSeen WHERE category = $1 AND NOT seen ORDER BY id ASC LIMIT 1)",
											 (category,))
	
def get(ident,tags,limit=9):
	category = hash(tags) % 0x7FFFFFFF
	arg = argbuilder()
	category = arg(category)
	stmt = Select(withtags.tagsWhat,InnerJoin(
					'randomSeen',InnerJoin('media','things',EQ('things.id','media.id')),
		EQ('randomSeen.media','media.id')),
								AND(
									"seen",
									AND(EQ('randomSeen.category',category),
											"randomSeen.id <= "+arg(ident))))
	stmt = Order(stmt,'randomSeen.id DESC')
	stmt = Limit(stmt,limit=limit)
	rows = db.execute(stmt.sql(),arg.args)
	#print('\n'.join(r[0] for r in rows))
	#raise SystemExit
	return rows

from redirect import Redirect
import time
from filedb import oj
import filedb

try:
	with open(oj(filedb.base,'nope.tags'),'rt') as inp:
		nopeTags = tagsModule.parse(inp.read())
except IOError:
	nopeTags = None

def zoop(params):
	zoop = dict((n,v[0]) for n,v in params.items() if n not in {'o','t'})
	zoop = urllib.parse.urlencode(zoop)
	return zoop

def maxident(category):
	return db.execute("SELECT MAX(id) FROM randomSeen WHERE category = $1 AND seen",
										(category,))[0][0]

def info(path,params):
	if 'q' in params:
		tags = tagsModule.parse(params['q'][0])
	else:
		tags = User.tags()
	if nopeTags: tags.update(nopeTags)
	category = hash(tags) % 0x7FFFFFFF
	if 'c' in params:
		if Session.prefetching: return ()
		#print(params)
		pickone(category, tags)
		dest = "../" + '{:x}'.format(maxident(category)) + "/"
		del params['c']
		params = zoop(params)
		if params:
			dest = dest + '?' + params
		raise Redirect(dest,code=302)
	ident = int(path[1],16);
	while True:
		links = get(ident,tags)
		if links: return ident,category,links
		if Session.prefetching: return ()
		pickone(tags)

from user import User
from session import Session
from pages import pagemaker,makePage,makeLinks,makeLink,Links

import note

import mydirty as d
import dirty.html as dd

import urllib.parse

@pagemaker
def page(info,path,params):
	with makePage("Random") as p:
		ident,category,links = info
		links = iter(links)
		medium,name,type,tags = next(links)
		fid,link,thing = makeLink(medium,type,name,False,0,0)
		if ident == maxident(category):
			params['c'] = ['1']
			params = zoop(params)
			print("ummm",params)
			Links.next = '?' + params
		else:
			Links.next = "../" + '{:x}'.format(ident+1) + '/'
		if ident > 0:
			Links.prev = "../" + '{:x}'.format(ident-1) + '/'

		d.p(dd.a('Another?',href=Links.next))
		d.p(dd.a(link,href='/art/~page/'+fid+'/'))
		with d.div(title='past ones'):
			makeLinks(links)

if __name__ == '__main__':
	from pprint import pprint
	import tags
	Session.prefetching = False
	tags = tags.parse('apple bloom, -sweetie belle, scootaloo')
	pickone(tags)
	pprint(get(tags))
	from eventlet.greenthread import sleep
	sleep(3)
