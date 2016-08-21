#!/usr/bin/env python3
if __name__ == '__main__':
	import sys,os
	sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from favorites.parseBase import *
from favorites import parsers
from dbqueue import top,fail,win,megafail,delay,host,remaining
import db

from multiprocessing import Process, Condition, Value, Event, Queue
from queue import Empty
import time
import fixprint

from ctypes import c_bool

PROGRESS, IDLE, DONE = range(3)

class Catchupper(Process):
	def __init__(self,provide_progress):
		super().__init__()
		self.done = Value(c_bool,False)
		self.provide_progress = provide_progress
		self.poked = Condition()
		self.q = Queue()
	def send_progress(self,block,total):
		self.q.put((PROGRESS,(block,total)))
	def run(self):
		if self.provide_progress:
			setupurllib.progress = self.send_progress
		db.reopen()
		try:
			import signal
			signal.signal(signal.SIGUSR1, lambda sig: None)
			# ehhhh done, before we start, to transmit remaining?
			self.q.put((DONE,remaining()))
			while True:
				self.q.put((IDLE,False))
				while self.squeak() is True:
					self.q.put((DONE,remaining()))
				self.q.put((IDLE,True))
				if self.done.value: break
				print('waiting for pokes')
				with self.poked:
					self.poked.wait()
		except SystemExit: pass
		except KeyboardInterrupt: pass
	def squeak(self,*a):
		uri = top()
		if uri is None:
			print('none dobu')
			if self.done.value: raise SystemExit
			return
		ah = alreadyHere(uri)
		if ah:
			print("WHEN I AM ALREADY HERE")
			if 'noupdate' in os.environ:
				win(uri)
				return True
		try:
			for attempts in range(2):
				print("Parsing",uri)
				try:
					parse(uri)
					win(uri)
					break
				except urllib.error.URLError as e:
					print(e.headers)
					print(e.getcode(),e.reason,e.geturl())
					if e.getcode() == 404: raise ParseError('Not found')
					time.sleep(3)
			else:
				print("Could not parse",uri)
		except ParseError:
			print('megafail')
			megafail(uri)
		except urllib.error.URLError as e:
			if e.getcode() == 503:
				print('site is bogged down! delaying a while')
				delay(uri,'1 minute')
			print('megafail error',e.getcode())
			megafail(uri)
		except urllib.error.HTTPError as e:
			if e.code == 400:
				print('uhm, forbid?')
			print(e,dir(e))
			raise SystemExit(23)
		except Exception as e:
			print("fail",uri,e)
			raise SystemExit(23)
			fail(uri)
			if not ah:
				import traceback,sys
				traceback.print_exc(file=sys.stdout)
				time.sleep(1)
		return True


class Catchup:
	PROGRESS = PROGRESS
	DONE = DONE
	IDLE = IDLE # meh
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
			self.process = Catchupper(self.provide_progress)
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
