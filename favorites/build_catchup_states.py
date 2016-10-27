to_client = ["PROGRESS", "IDLE", "COMPLETE", "DONE"]
to_server = ["POKE","ENABLE_PROGRESS"]

def dictify(l):
	num = 0
	d = {}
	for name in l:
		d[name] = num
		num += 1
	return d
to_client = dictify(to_client)
to_server = dictify(to_server)

to_server["DONE"] = to_client["DONE"]

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
			for name,num in names.items():
				out.write(name+" = "+str(num)+"\n")
			out.write("lookup_"+type+" = {\n")
			num = 0
			for num,name in names.items():
				out.write("\t"+repr(num)+": " + repr(name) + ",\n")
				num += 1
			out.write("\t"+repr(messages["DONE"])+": \"DONE\"\n")
			out.write("}\n\n")

