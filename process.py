import user as derp
import tags as tagsModule
import db
from note import note

def user(path,params,data):
	assert(data is None)
	params = dict(params)
	note('updating user',params)
	def check(name):
		l = params.get(name)
		if l:
			return l[0]
	def checkB(name):
		if check(name):
			return True
		return False

	rescale_width = check('rescale_width')
	if rescale_width:
		rescale_width = int(rescale_width)
		if rescale_width > 2048:
			rescale_width = 2048
		elif rescale_width < 400:
			rescale_width = 400
	else:
		rescale_width = 800
	assert rescale_width
	news = {
		'rescaleimages': checkB('rescale'),
		'nocomics': checkB('comic'),
		'navigate': checkB('navigate'),
		'loadjs': checkB('loadjs'),
		'rescale_width': rescale_width,
	}

	newtags = check('tags')
	note('updating user tags',newtags)
	news['defaultTags'] = False
	
	self = derp.currentUser()
	with db.transaction():
		# XXX: tasteless
		db.execute("DELETE FROM uzertags WHERE uzer = $1",(self.id,))

		if newtags:
			tags = tagsModule.parse(newtags[0])
			if tags.posi:
				db.execute('INSERT INTO uzertags (tag,uzer,nega) SELECT unnest(array(SELECT unnest($1::INTEGER[]) EXCEPT SELECT tag FROM uzertags WHERE uzer = $2)),$2,FALSE',(tags.posi,self.id))
			if tags.nega:
				db.execute('INSERT INTO uzertags (tag,uzer,nega) SELECT unnest(array(SELECT unnest($1::INTEGER[]) EXCEPT SELECT tag FROM uzertags WHERE uzer = $2)),$2,TRUE',(tags.nega,self.id))
		db.execute('UPDATE uzers SET defaultTags = FALSE WHERE id = $1',(self.id,))
		derp.set(news.items())
	return ""
