ident = input("ID: ")
ident = ident.rstrip("/").rsplit('/',1)[-1]
ident = int(ident,0x10)
print("ID is ",hex(ident))
url = input("URL: ")

import syspath
import db
from favorites.parse import finders, parse

for name, matcher, handlers in finders:
	if not matcher(url): continue
	
	if 'normalize' in handlers:
		url = handlers['normalize'](url)
		print("Normalized URL",url);
	break

db.execute("SELECT addsource($1::bigint,$2::text)",(ident,url))

# get new tags:
parse(url)
