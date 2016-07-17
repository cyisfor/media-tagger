from ctypes import *
lib = cdll.LoadLibrary("./libparseui.so")

class parseui:
	def quit(self, on_quit):
		self.on_quit = on_quit
		return on_quit
	def clicked(self, on_clicked):
		self.on_clicked = on_clicked
		return on_clicked
	def launch(self):
		lib.parseui_launch(self.on_clicked, self.on_quit)
	
