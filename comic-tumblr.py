from setupurllib import myretrieve

import re

up_resolution = re.compile("([0-9]+)(\.[^\.]+)")
def upres(m):
	num = int(m.group(1))
	if num < 1280:
		return "1280" + m.group(2)
	return m.group(0)

import sys
readline = sys.stdin.readline

while True:
	link = readline()
	
	while True:
		image = readline()
		if not image: break
		image = re.sub(up_resolution,upres,image)
		print(image,link)
		continue
		def download(dest):
			response = myretrieve(Request(image,headers,dest))
			return response.modified, response["Content-Type"]
		id, was_created = create.internet(download,image,tags,image,(link,))
