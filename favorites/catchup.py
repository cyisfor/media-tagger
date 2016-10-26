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

PROGRESS, IDLE, COMPLETE, DONE = range(4)
POKE,  = range(1)

class Catchupper:
	def __init__(self,q,provide_progress=None):
		print("Starting up catchup backend")
		self.provide_progress = provide_progress
		self.q = q
		import db
		from favorites.dbqueue import remaining
		db.reopen()
		self.send(COMPLETE,"H",remaining())
		self.squeak()
	def send(self,message,pack,*a):
		self.q.send(struct.pack("B"+pack,message,*a))
	def __call__(self,message):
		message = struct.unpack("B",message)
		print("catchup message",message)
		if message == POKE:
			self.squeak()
		elif message == DONE:
			self.send(DONE,"")
			raise SystemExit
	def squeak(self):
		self.send(IDLE,"B",0)
		try:
			while self.catch_one() is True:
				from favorites.dbqueue import remaining
				self.send(COMPLETE,"H",remaining())
		finally:
			self.send(IDLE,"B",1)
	def send_progress(self,block,total):
		self.send(PROGRESS,"HH",block,total)
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
						parse(uri)
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

def catchup(provide_progress=None):
	q = node.connect_silly("catchup",lambda q: Catchupper(q,provide_progress))
	class Poker:
		def poke():
			q.send(struct.pack("B",POKE))
		def stop():
			q.send(struct.pack("B",DONE))
		def run(on_message):
			return q.read_all(on_message)
	return Poker

if __name__ == '__main__':
	# just run the backend, leave the rest alone
	poker = catchup()
	if "stop" in os.environ:
		poker.stop()
		@poker
		def _(message):
			print(message)
			raise SystemExit
	raise SystemExit
else:
	import sys
	sys.modules[__name__] = catchup
