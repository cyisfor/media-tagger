from versions import versioner
import db
version = Versioner('explanations')

@version(1)
def _():
    db.vsetup(*db.source('sql/explanations.sql'))

def explain(id):
    return db.execute('SELECT x,y,r,text FROM explanations WHERE image = $1',
                      (id,))
