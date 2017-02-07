ident = input("ID: ")
ident = ident.rstrip("/").rsplit('/',1)[-1]
ident = int(ident,0x10)
print("ID is ",hex(ident))
url = input("URL: ")

import syspath
import db
from favorites.parse import normalize, parse
from favorites import parsers as _
url = normalize(url)
print("Normalized URL",url);

db.execute("SELECT addsource($1::INTEGER,$2::text)",(ident,url))

# get new tags:
parse(url)
