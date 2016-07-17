#!/usr/bin/python3
import db

def setup():
	db.setup("""CREATE TABLE desktops (
id bigint PRIMARY KEY REFERENCES images(id),
selected timestamptz DEFAULT clock_timestamp() NOT NULL)""",
	"CREATE UNIQUE INDEX orderDesktops ON desktops (selected DESC)");

def history(n=0x10):
	return [row[0] for row in db.execute("SELECT id FROM desktops ORDER BY selected DESC LIMIT $1",(n,))]

def next(clean=True,tries=0):
	r = db.execute("""INSERT INTO desktops (id)
	SELECT images.id FROM images INNER JOIN things ON images.id = things.id
	WHERE images.id NOT IN (SELECT id FROM desktops)
		AND ( (NOT $1) OR (
				neighbors && array(SELECT id FROM tags WHERE name IN
					('special:safe','rating:safe','clean'))) )
		AND NOT neighbors && array(SELECT id FROM tags
			WHERE name = 'special:rl')
		AND height > 600
		AND width > 800
		AND ratio < 1.8
		AND ratio > 0.8
		ORDER BY random() LIMIT 1 RETURNING desktops.id""",(clean,))
	if not r:
		if tries >= 2:
			raise RuntimeError("Couldn't find any desktops!!")
		db.execute("DELETE FROM desktops")
		return next(clean,tries+1)
	return r[0][0]

if __name__ == '__main__':
	import shutil,os,filedb
	setup()
	id = next()
	desktop = os.path.expanduser("/home/.config/desktop")
	try: os.unlink(desktop)
	except OSError: pass
	# Can't use filedb.mediaPath why...?
	src = os.path.join(filedb.top,"media",'{:x}'.format(id))
	os.chdir("/home/tmp")
	try: os.mkdir("ipfs")
	except OSError: pass
	os.chdir("ipfs")
	name = db.execute("SELECT name FROM media WHERE id = $1",(id,))[0][0];
	shutil.copy2(src,name)
	with open('index.html.temp','wt') as out:
		out.write('''<html><head><title>cy's Current Desktop</title></head>
		<body>
		<p>Hi I'm cy. I hang around on <a href="https://www.hypeirc.net/">#hyperboria</a> and <a href="https://derpibooru.org">derpibooru</a>. Mostly I write <a href="https://critter.cloudns.org/stories/html/">stories</a> about ponies. Anyway, here's my current (randomly selected once an hour) desktop wallpaper:</p>
		<p><img src="'''+name+'''"/></p>
		</body></html>''')
	os.rename('index.html.temp','index.html')
	try:
		import subprocess as s
		out,err = s.Popen(["ipfs","add","--recursive","--quiet",'.'],
											stdout=s.PIPE).communicate()
		out = out.decode().rstrip()
		hashes = out.split('\n')
		s.call(["ipfs","name","publish","--lifetime=1h","/ipfs/"+hashes[-1]])
	except FileNotFoundError: pass
	shutil.copy2(src,desktop)
	if not os.environ.get('DISPLAY'):
		os.environ['DISPLAY'] = ':0.0'
	os.environ.setdefault('XAUTHORITY','/home/.Xauthority')
	os.execlp("xfdesktop","xfdesktop","--reload")
