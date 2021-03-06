from versions import Versioner
import db
version = Versioner('explanations')

@version(1)
def _():
    stmts = db.source('sql/explanations.sql',namedStatements=False)
    print(stmts)
    db.vsetup(*stmts)

@version(2)
def _():
	db.setup("CREATE UNIQUE INDEX unique_explanations ON explanations(image,top,derpleft,w,h)")
		
version.setup()

def explain(id):
    return db.execute('SELECT id,top,derpleft,w,h,script FROM explanations WHERE image = $1',
                      (id,))
