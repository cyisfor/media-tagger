#!/usr/bin/python3

import note
import create
import withtags
import filedb
import db
import better.stdin
import better.print

from hashlib import md5 as MD5

import codecs
import shutil
import datetime
import sys,os

def mysplit(s,cs):
	pending = ''
	for c in s:
		if c in cs:
			if pending:
				try: int(pending)
				except ValueError as e:
					# only yield if NOT an integer
					yield pending
			pending = ''
		else:
			pending += c
	if pending:
		try: int(pending)
		except ValueError as e:
			yield pending

boring = set(["the","for","this","and","not","how","are","files","xcf","not","my","in"])

def discover(path):
	discovered = set()

	if path[0] == b'/'[0]:
		for start in (os.path.expanduser("~/art/"),'/home/extra/youtube'):
			relpath = os.path.relpath(path,start.encode('utf-8'))
			if not b'..' in relpath: break
		else: raise ImportError("Can't import path "+str(path))
		name = os.path.basename(relpath)
		relpath = relpath.decode('utf-8')
		name = name.decode('utf-8')
	else:
		print('nob')
		relpath = name = path.decode('utf-8')

	officialTags = False
	if ' - ' in name:
		tags,rest = name.split(' - ',1)
		if not '-' in tags:
			print('found official tags header',tags)
			print(rest)
			officialTags = True
			discovered = set(tag.strip() for tag in tags.split(','))
			name = rest
			
	discovered = discovered.union(mysplit(relpath[:relpath.rfind('.')].lower(),'/ .-_*"\'?()[]{},'))
	discovered = set([comp for comp in discovered if len(comp)>2 and comp not in boring])

	return discovered,name

def main():
	cod = codecs.lookup('utf-8')
	implied = set()
	for tag in os.environ['tags'].split(','):
		tag = tag.strip()
		implied.add(tag)
	try:
		db.execute("CREATE TABLE badfiles (path TEXT PRIMARY KEY)")
	except: pass
	
	sources = None
	recheck = os.environ.get('recheck')
	def check(path,name):
		if sources:
			source = sources.get(name)
		else:
			source = None
		#bpath,length = cod.encode(path,'surrogateescape')
		#if length!=len(path):
		#	raise Exception("Bad path? ",path[:length],'|',repr(path[length:]))
		#print(implied.union(discovered))
		path = path.encode('utf-8')
		print(path)
		impmort(path,implied,recheck=recheck,urisource=source)

	vtop = '.'
	for top,dirs,ns in os.walk(vtop):
		print('in',os.path.abspath(top))
		if 'sources.db' in ns:
			print("found a sources database!")
			if sources: sources.close()
			import dbm
			sources = dbm.open(os.path.join(top,'sources.db'),'r',0o644)
			ns.remove('sources.db')		
		for name in ns:
			if name in {'html'}: continue
			check(os.path.abspath(os.path.join(vtop,top,name)),name)

def impmort(path,implied,recheck=False,urisource=None):
	bad = db.execute("SELECT COUNT(path) FROM badfiles WHERE path = $1",(path,))
	if bad[0][0] != 0: return
	idnum = None
	source = db.execute("SELECT id FROM filesources WHERE path = $1",(path,))
	try:
		with db.transaction():
			if source:
				source = source[0][0]
				idnum = db.execute("SELECT id,hash FROM media WHERE sources @> ARRAY[$1::int]",(source,))
				if idnum:
					idnum,hash = idnum[0]
					if not recheck: #(officialTags or recheck):
						# array_length returns NULL for 0-sized arrays, never 0
						neighbors = db.execute("SELECT array_length(neighbors,1)::int FROM things WHERE id = $1",
																	 (idnum,))
						if neighbors and neighbors[0][0]:
							return
						else:
							note("need recheck for empty tags",hex(idnum))
			else:
				source = db.execute("INSERT INTO sources (hasTags) VALUES (TRUE) RETURNING id")[0][0]
				db.execute("INSERT INTO filesources (id,path) VALUES ($1,$2)",(source,path))
			source = create.Source(source,hasTags=True)
			if not idnum:
				with open(path,'rb') as inp:
					hash = create.mediaHash(inp)
				idnum = db.execute("SELECT id FROM media WHERE hash = $1",(hash,))
				if idnum: idnum = idnum[0][0]
				print("Hasho",idnum)
			try: discovered,name = discover(path)
			except ImportError: return
			if urisource:
				urisource = create.Source(urisource,hasTags=True)
			alltags = implied.union(discovered)
			assert alltags, "no tags found for " + path
			if idnum:
				note("Adding source",idnum,source)
				sources = [source]
				if urisource:
					sources.append(urisource)
				create.update(idnum,
				              sources,
				              alltags,
				              name)
			else:
				print("importing",path,discovered)
				if urisource:
					sources = (urisource,)
				else:
					sources = ()
				create.internet(create.copyMe(path),
				                source,
				                alltags,
				                source,
				                sources,
				                name=name)
	except create.NoGood: 
		db.execute("INSERT INTO badfiles (path) VALUES ($1)",(path,))

if __name__ == '__main__': main()
