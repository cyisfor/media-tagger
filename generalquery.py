import db,filedb

import sys,os

print('<html><head></head><body>')
host = 'http://[fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c]'

for row in db.c.execute(sys.stdin.read()):
    id = row[0]
    filedb.check(id)
    print('<a href="%s/art/~page/%x/"><img src="%s/thumb/%x"/></a>' % (host,id,host,id))

print('</body>')
