#!/usr/bin/env python3
if __name__ == '__main__':
	import sys,os
	import syspath

import note

import imagecheck

from favorites.parse import alreadyHere,parse,ParseError
from favorites import parsers
from favorites.dbqueue import top,fail,win,megafail,delay,host,remaining
import db

import json.decoder
from multiprocessing import Process, Condition, Value, Event, Queue
from queue import Empty
import time
import fixprint

from ctypes import c_bool

PROGRESS, IDLE, COMPLETE, DONE = range(4)

class Catchupper(Process):
	def __init__(self,provide_progress=None):
		super().__init__()
		self.done = Value(c_bool,False)
		self.provide_progress = provide_progress
		self.poked = Condition()
		self.q = Queue()
	def send_progress(self,block,total):
		self.q.put((PROGRESS,(block,total)))
	def run(self):
		import urllib.error

		if self.provide_progress:
			import setupurllib
			setupurllib.progress = self.send_progress
		db.reopen()
		try:
			import signal
			signal.signal(signal.SIGUSR1, lambda sig: None)
			# ehhhh a done, before we start, to transmit remaining?
			self.q.put((COMPLETE,remaining()))
			while True:
				self.q.put((IDLE,False))
				while self.squeak() is True:
					self.q.put((COMPLETE,remaining()))
				self.q.put((IDLE,True))
				if self.done.value: break
				print('waiting for pokes')
				with self.poked:
					self.poked.wait()
		except SystemExit: pass
		except KeyboardInterrupt: pass
		finally:
			self.q.put(DONE)
	def squeak(self,*a):
		import urllib.error
		import setupurllib
		uri = top()
		if uri is None:
			print('none dobu')
			if self.done.value: raise SystemExit
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


class Catchup:
	PROGRESS = PROGRESS
	COMPLETE = COMPLETE
	IDLE = IDLE # meh
	DONE = DONE # mehhh
	# provide_progress=True means we'll pull from self.progress
	def __init__(self,provide_progress=False):
		self.provide_progress = provide_progress
		self.start()
	def start(self):
		self.process = Catchupper(self.provide_progress)
		self.process.start()
		self.terminate = self.process.terminate
		self.get = self.process.q.get
	def poke(self):
		print('poke')
		if not self.process.is_alive():
			print('died?')
			self.start()
		try:
			with self.process.poked:
				self.process.poked.notify_all()
		except AssertionError:
			# bug...
			self.process.terminate()
			self.process = Catchupper(self.provide_progresss)
			self.start()
	def finish(self):
		self.process.done.value = True
		while True:
			self.poke()
			try:
				while True:
					print('ignored message',self.process.q.get(False))
			except queue.Empty: pass
			self.process.join(1)
			if not self.is_alive(): break
			self.process.done.value = True

if __name__ == '__main__':
	# no subprocess here

	instance = Catchupper()
	while instance.squeak() is True: pass
else:
	import sys
	sys.modules[__name__] = Catchup
