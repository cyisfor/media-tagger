from setupurllib import myretrieve
import tags,comic

import re
from functools import partial

up_resolution = re.compile("([0-9]+)(\.[^\.]+)")
def upres(m):
	num = int(m.group(1))
	if num < 1280:
		return "1280" + m.group(2)
	return m.group(0)

import sys,os
readline = sys.stdin.readline

title = readline()
def derp():
	t = tags.parse(readline())
	t.posi.add(tags.makeTag("tumblr"))
	t.posi.add(tags.makeTag("comic"))
	return t
tags = derp()

def description():
	for line in sys.stdin:
		print('uhh',line)
		if line == '.\n': return
		yield line
description = ''.join(description())

@partial(comic.findComicByTitle,title)
def c(handle):
	handle(description)

print((title,tags,description,hex(c)))
raise SystemExit

main_link = None
	
while True:
	link = readline().rstrip()
	if main_link is None:
		main_link = link
	if not link: break
	headers = {'Referer': link}
	
	while True:
		image = readline().rstrip()
		if not image: break
		image = re.sub(up_resolution,upres,image)
		def download(dest):
			response = myretrieve(Request(image,headers,dest))
			return response.modified, response["Content-Type"]
		id, was_created = create.internet(download,image,tags,image,set((main_link,link)))
