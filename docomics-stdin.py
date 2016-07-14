# ugh
from favorites.parseBase import parse,normalize,ParseError
import comic
from redirect import Redirect

c = os.environ.get('comic')
w = os.environ.get('which',0)

for url in sys.stdin:
	try:
		m = parse(normalize(url),noCreate=True)
		if not m:
			print('uhhh',url)
	except ParseError:
		try: m = int(url.rstrip('/').rsplit('/',1)[-1],0x10)
		except ValueError:
			print('nope')
			return	
	if c is None:
		c = db.execute('SELECT comic,which FROM comicpage WHERE medium = $1 ORDER BY which DESC',(m,))
		if len(c)>0:
			c = c[0]
			c,w = c
		else:
			c = db.execute('SELECT MAX(id)+1 FROM comics')[0][0]
			def getinfo(next):
				title = input('title')
				description = input('description')
				source = input('source')
				tags = input("tags")
				next(title,description,source,tags)
			comic.findInfo(c,getinfo)
			w = db.execute('SELECT MAX(which)+1 FROM comicpage WHERE comic = $1',(c,))
			if w[0][0]:
				w = w[0][0]
			else:
				w = 0
	print('comic',c,'page',w,'is',hex(m))
	try:
		comic.findMedium(c,w,m)
	except Redirect: pass
