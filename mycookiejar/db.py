db = None

import os
verbose = 'db_verbose' in os.environ

def execute(stmt,args=()):
	if verbose:
		print(stmt)
		print(args)
	return db.execute(stmt,args)
