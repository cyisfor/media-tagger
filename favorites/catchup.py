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
	def __init__(self,q):
		print("Starting up catchup backend")
		self.q = q
		import db
		from favorites.dbqueue import remaining
		db.reopen()
		self.send(COMPLETE,"H",remaining())
		self.squeak()
	def send(self,message,pack,*a):
		note("sending",lookup_client[message])
		self.q.send(struct.pack("=B"+pack,message,*a))
	def handle_regularly(self,message):
		message = message[0]
		note("received",lookup_server[message])
		if message == POKE:
			self.squeak()
		elif message == DONE:
			print("done")
			self.send(DONE,"")
			raise SystemExit
	def __call__(self, message):
		# some messages only need to get sent as initialization
		if message == ENABLE_PROGRESS:
			self.provide_progress = True
		else:
			self.__call__ = self.handle_regularly
			return self.handle_regularly(message)
	def squeak(self):
		self.send(IDLE,"B",0)
		try:
			while self.catch_one() is True:
				from favorites.dbqueue import remaining
				self.send(COMPLETE,"H",remaining())
		finally:
			self.send(IDLE,"B",1)
	def send_progress(self,block,total):
		self.send(PROGRESS,"II",block,total)
	def catch_one(self,*a):
		from favorites.parse import alreadyHere,parse,ParseError
		from favorites import parsers
		from favorites.dbqueue import top,fail,win,megafail,delay,host
		import imagecheck

		import json.decoder
		import urllib.error
		import setupurllib
		uri = top()
		if uri is None:
			print('none dobu')
			return
		ah = alreadyHere(uri)
		if ah:
			import os
			if 'noupdate' in os.environ:
				print("WHEN I AM ALREADY HERE",uri)
				win(uri)
				return True
		try:
			try:
				for attempts in range(2):
					print("Parsing",uri)
					try:
						parse(uri,progress=self.send_progress if self.provide_progress else None)
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

def catchup(provide_progress=False):
	q = node.connect_silly("catchup",lambda q: Catchupper(q))
	def send(what):
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

if __name__ == '__main__':
	# just run the backend, leave the rest alone
	poker = catchup()
	if "stop" in os.environ:
		poker.stop()
		@poker.run
		def _(message):
			if message[0] == DONE:
				raise SystemExit
	raise SystemExit
else:
	import sys
	sys.modules[__name__] = catchup
