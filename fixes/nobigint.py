import os

def fix(script,out):
	if not 'bigint' in script: return False
	out.write(script.replace("bigint","INTEGER"))
	return True
	

for top,ds,ns in os.walk("."):
	for n in ns:
		if n.endswith(".py"):
			with open(path) as inp:
				script = inp.read()
			with open("tmp","wt") as out:
				if not fix(script,out):
					continue
			os.rename("tmp",path)
