from setupurllib import myretrieve
import tags,comic

import re

up_resolution = re.compile("([0-9]+)(\.[^\.]+)")
def upres(m):
	num = int(m.group(1))
	if num < 1280:
		return "1280" + m.group(2)
	return m.group(0)

import sys,os
readline = sys.stdin.readline

title = readline()
def description():
	for line in readline():
		if line == '.\n': return
		yield line
description = ''.join(description())
tags = tags.parse(readline())
tags.posi

@partial(comic.findComicByTitle,title)
def c(handle):
	handle(description)

while True:
	link = readline().rstrip()
	if not link: break
	headers = {'Referer': link}
	
	while True:
		image = readline().rstrip()
		if not image: break
		image = re.sub(up_resolution,upres,image)
		def download(dest):
			response = myretrieve(Request(image,headers,dest))
			return response.modified, response["Content-Type"]
		id, was_created = create.internet(download,image,tags,image,(link,))
