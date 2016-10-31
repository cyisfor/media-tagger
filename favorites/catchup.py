#!/usr/bin/env python3
if __name__ == '__main__':
	import sys,os
	import syspath

import node
import note

import time
import fixprint
import struct

from ctypes import c_bool

from favorites.build_catchup_states import *

class Catchupper:
	provide_progress = False
	def __init__(self):
		import db
		from favorites.dbqueue import remaining
		db.reopen()
	def stop(self):
		raise SystemExit
	def poke(self):
		self.idle(False)
		try:
			while self.catch_one() is True:
				from favorites.dbqueue import remaining
				self.complete(remaining())
		finally:
			self.idle(False)
	def catch_one(self,*a):
		from favorites.parse import alreadyHere,parse,ParseError
		from favorites import parsers
		from favorites.dbqueue import top,fail,win,megafail,delay,host
		import imagecheck

		import json.decoder
		import urllib.error
		import setupurllib
		uri = top()
		note.yellow(uri)
		if uri is None:
			return
		ah = alreadyHere(uri)
		if ah:
			import os
			if 'noupdate' in os.environ:
				note.red("WHEN I AM ALREADY HERE",uri)
				win(uri)
				return True
		try:
			try:
				for attempts in range(2):
					note("Parsing",uri)
					try:
						parse(uri,progress=self.progress if self.provide_progress else None)
						win(uri)
						break
					except urllib.error.URLError as e:
						note(e.headers)
						note(e.getcode(),e.reason,e.geturl())
						if e.getcode() == 404: raise ParseError('Not found')
						time.sleep(3)
				else:
					print("Could not parse",uri)
			except (ParseError,imagecheck.NoGood):
				print('megafail')
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
				print('megafail error',e.code)
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
			print(e)
			raise
		except json.decoder.JSONDecodeError:
			megafail(uri)
			print("No JSON at this URI?",uri)
		except Exception as e:
			print("huh?",uri,type(e))
			raise
		return True

class BackendCatchupper(Catchupper):
	def __init__(self,q):
		self.q = q
	def send(self,message,pack,*a):
		note("sending",lookup_client[message],a)
		self.q.send(struct.pack("=B"+pack,message,*a))
	def __call__(self, message):
		message = message[0]
		note("received",lookup_server[message])
		if message == POKE:
			self.poke()
		elif message == DONE:
			self.send(DONE,"")
			raise SystemExit
		elif message == ENABLE_PROGRESS:
			note.yellow("enabling progress")
			self.provide_progress = True
	def progress(self,block,total):
		self.send(PROGRESS,"II",block,total)
	def complete(self,remaining):
		send(COMPLETE,"H",remaining)

def catchup(provide_progress=False,dofork=True):
	q = node.connect_silly("catchup",BackendCatchupper,dofork=dofork)
	def send(what):
		note.red("SEND",what,lookup_server[what])
		q.send(struct.pack("B",what))
	if provide_progress:
		send(ENABLE_PROGRESS)
	class Poker:
		def poke():
			send(POKE)
		def stop():
			send(DONE)
		def run(on_message=None):
			return q.read_all(on_message)
	return Poker

def derp_catchup(provide_progress=False,dofork=True):
	c = Catchupper()
	c.provide_progress = provide_progress
	return c
if __name__ == '__main__':
	# just run the backend, leave the rest alone
	poker = catchup(dofork=('nofork' not in os.environ))
	if "stop" in os.environ:
		poker.stop()
		@poker.run
		def _(message):
			if message[0] == DONE:
				raise SystemExit
	poker.poke()
	@poker.run
	def _(message):
		print(message)
else:
	import sys
	sys.modules[__name__] = catchup
