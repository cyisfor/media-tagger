to_client = ["PROGRESS", "IDLE", "COMPLETE"]
to_server = ["POKE","ENABLE_PROGRESS"]
to_both = ["DONE","STATUS"]

def dictify(l):
	num = 0
	class derp(dict):
		_keys = l
	d = derp()
	for name in l:
		d[name] = num
		num += 1
	return d
to_client = dictify(to_client + to_both)
to_server = dictify(to_server)

for key in to_both:
	to_server[key] = to_client[key]
	to_server._keys.append(key)

def undictify(d):
	l = []
	# please keep keys in above order
	for k in d._keys:
		l.append((k,d[k]))
	return l
to_server = undictify(to_server)
to_client = undictify(to_client)

import sys,os
here = sys.modules[__name__].__file__
heremod = os.stat(here).st_mtime

import filedb
other = os.path.join(filedb.temp,"catchup_states.py")
try: othermod = os.stat(other).st_mtime
except: othermod = None
if othermod is None or othermod < heremod:
	# need update
	with open(other,"wt") as out:
		for type,names in (("client",to_client),("server",to_server)):
			for name,num in names:
				out.write(name+" = "+str(num)+"\n")
			out.write("lookup_"+type+" = {\n")
			for num,name in names:
				out.write("\t"+repr(name)+": " + repr(num) + ",\n")
			out.write("}\n\n")

import sys
sys.path.append(filedb.temp)
from catchup_states import *
sys.path = sys.path[:-1]
