#!/usr/bin/env python3
if __name__ == '__main__':
	import sys,os
	import syspath

import note

from favorites.launch.protocol import as_catchup

import time
from better import print as _
import struct

from ctypes import c_bool

running = False
def run():
	global running
	if running:
		return True
	running = True
	from random import randint
	print("running!")
	if randint(0,50) == 0:
		raise RuntimeError("derp")
	while True:
		derp = catch_one()
		if not derp: break
		if derp is True: continue
		#ident,medium,wasCreated = derp
		#from favorites.dbqueue import remaining
		#yield ident,medium,wasCreated
	running = False
	return True

progress = as_catchup(run)
		
def catch_one():
	from favorites.parse import alreadyHere,parse,ParseError
	from favorites import parsers
	from favorites.dbqueue import top,fail,win,megafail,delay,host
	import imagecheck

	import json.decoder
	import urllib.error
	import setupurllib
	res = top()
	if res is None:
		return
	ident,uri = res
	note.yellow(uri)
	if uri.startswith("http://[fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c]"):
		megafail(uri)
		return True
	ah = alreadyHere(uri)
	if ah:
		medium, wasCreated = ah
		import os
		if 'noupdate' in os.environ:
			note.red("WHEN I AM ALREADY HERE",uri)
			win(medium,uri)
			return ident,medium,wasCreated
	try:
		try:
			import db # .Error
			progress.starting(ident)
			for attempts in range(2):
				note("Parsing",uri)
				try:
					medium,wasCreated = parse(uri,progress=progress.progressed)
					win(medium,uri)
					progress.done()
					return ident,medium,wasCreated
				except urllib.error.URLError as e:
					note(e.headers)
					note(e.getcode(),e.reason,e.geturl())
					if e.getcode() == 404: raise ParseError('Not found')
					if e.getcode() == 403: raise ParseError('Forbidden')
					time.sleep(3)
				except db.Error as e:
					note.alarm(e.info['message'])
					if b'25P02' in e.info['message']:
						# aborted transaction... let's fix that
						db.retransaction()
			else:
				print("Could not parse",uri)
				progress.done()
		except (ParseError,imagecheck.NoGood) as e:
			note('megafail',e)
			megafail(uri)
			return True
		except setupurllib.URLError as e:
			raise e.__cause__
	except urllib.error.HTTPError as e:
		note(type(e))
		if e.code == 503:
			print('site is bogged down! delaying a while')
			delay(uri,'1 minute')
		else:
			note('megafail error',e.code)
			raise SystemExit(23)
			#megafail(uri)
		if e.code == 400:
			print('uhm, forbid?')
		time.sleep(1)
	except urllib.error.URLError as e:
		e = e.args[0]
		if type(e) == ConnectionRefusedError:
			note('connection refused')
			fail(uri)
			return True
		note.error(e)
		raise
	except json.decoder.JSONDecodeError:
		megafail(uri)
		print("No JSON at this URI?",uri)
	except Exception as e:
		print("huh?",uri,type(e))
		raise
	return True

if __name__ == '__main__':
	from gi.repository import GLib
	loop = GLib.MainLoop()
	GLib.idle_add(lambda: run() and False)
	GLib.timeout_add_seconds(20,run)
	loop.run()
