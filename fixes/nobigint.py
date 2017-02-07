import os

def fix(script,path):
	if not 'bigint' in script: return
	with open("tmp","wt") as out:
		out.write(script.replace("bigint","INTEGER"))
	os.rename("tmp",path)

for top,ds,ns in os.walk("."):
	for n in ns:
		if n == "nobigint.py": continue # yeah...
		if n.endswith(".py"):
			with open(path) as inp:
				script = inp.read()
			fix(script,path)
