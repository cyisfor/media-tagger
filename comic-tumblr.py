from setupurllib import myretrieve,Request
import tags,comic,create

import re
from functools import partial
from itertools import count

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
		if line == '.\n': return
		yield line
description = ''.join(description())

@partial(comic.findComicByTitle,title)
def c(handle):
	handle(description)

import db
db.execute("UPDATE comics SET description = $2 WHERE id = $1",(c,description))

print(title,hex(c))

main_link = None

whiches = count(0)

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
			response = myretrieve(Request(image,headers),dest)
			return response.modified, response["Content-Type"]
		which = next(whiches)
		print("Trying for",which,image)
		derpimage = create.Source(image)
		medium, was_created = create.internet(download,
																					derpimage,
																					tags,
																					derpimage,
																					(create.Source(link) for link in set((main_link,link))))
		comic.findMedium(c,which,medium)
