import user as derp
import tags as tagsModule
import db
from note import note

def user(path,params,data):
	assert(data is None)
	params = dict(params)
	note('updating user',params)
	rescale = params.get('rescale')
	if rescale:
		rescale = rescale[0]
		if rescale:
			rescale = True
		else:
			rescale = False
	else:
		rescale = False
	news = {
		'rescaleimages': rescale
	}
	comic = params.get('comic')
	if comic:
		comic = comic[0]
		if comic:
			noComics = False
		else:
			noComics = True
		news['noComics'] = noComics
	newtags = params.get('tags')	
	note('updating user tags',newtags)
	news['defaultTags'] = False
	
	self = derp.currentUser()
	with db.transaction():
		# XXX: tasteless
		db.execute("DELETE FROM uzertags WHERE uzer = $1",(self.id,))

		if newtags and newtags[0] and len(newtags[0]) > 0:
			tags = tagsModule.parse(newtags[0])
			if tags.posi:
				db.execute('INSERT INTO uzertags (tag,uzer,nega) SELECT unnest(array(SELECT unnest($1::bigint[]) EXCEPT SELECT tag FROM uzertags WHERE uzer = $2)),$2,FALSE',(tags.posi,self.id))
			if tags.nega:
				db.execute('INSERT INTO uzertags (tag,uzer,nega) SELECT unnest(array(SELECT unnest($1::bigint[]) EXCEPT SELECT tag FROM uzertags WHERE uzer = $2)),$2,TRUE',(tags.nega,self.id))
		db.execute('UPDATE uzers SET defaultTags = FALSE WHERE id = $1',(self.id,))
	derp.set(news.items())
	return ""
