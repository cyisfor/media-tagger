import db

db.execute('''UPDATE media as top SET added = (SELECT added+(random()/100 || 'seconds')::interval from media where id = (select min(id) from media as bottom where added IS NOT NULL AND top.id < bottom.id)) where added IS NULL''')

db.execute('SELECT resultcache.expirequeries()')
