import db

import sys,os

paths = tuple(l.strip() for l in sys.stdin.readlines())

ids = db.execute('SELECT filesources.path,media.id FROM filesources INNER JOIN media ON filesources.id = ANY(media.sources) WHERE path = ANY($1)',
                 (paths,))
ids = dict(ids)
for path in paths:
	print("{:x}".format(ids[path]))

