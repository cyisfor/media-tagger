to_client = ["PROGRESS", "IDLE", "COMPLETE", "DONE"]
to_server = ["POKE","ENABLE_PROGRESS","EHUNNO", "DONE"]

import sys,os
here = sys.modules[__name__]
heremod = os.stat(here).st_mtime

import filedb
other = os.path.join(filedb.temp,"catchup_states.py")
othermod = os.stat(other).st_mtime
if othermod < heremod:
	# need update
	with open(other,"wt") as out:
		messages = dict()
		for type,names in (("client",to_client),("server",to_server)):
			num = 0
			for name in names:
				out.write(name+" = "+str(num)+"\n")
				num += 1
			out.write("lookup_"+type+" = {\n")
			for name in names:
				out.write("\t"+repr(num)+": " + repr(name) + ",\n")
			out.write("}")

