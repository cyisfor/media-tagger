from setupurllib import myretrieve,Request
import os
import filedb
import urllib.parse

base = os.path.join(filedb.base,"websites","stableQuest") # ehh...
os.makedirs(base)
os.chdir(base)
start = 'http://neonovus.tk/StableQuest%20-%20Index.htm'
prev = None
cur = start

def page_name(which):
	if which == 0: return 'index'
	return 'page{}'.format(which)

for which in count(0):
	if prev:
		req = Request(cur,headers={"Referer": prev})
	else:
		req = cur
	dest = page_name(which)+".html")
	if os.path.exists(dest):
		with open(dest) as inp:
			doc = BeautifulSoup(inp)
	else:
		with open("temp","wt+") as out:
			myretrieve(req,out)
			out.seek(0,0)
			doc = BeautifulSoup(out)
		os.rename("temp",dest)

	e = doc.find('div',id='navigation')
	e = e.find(attr={'class': 'nav'},alt="Next page")
	e = e.parent
		
	prev = cur
	cur = urllib.parse.urljoin(cur,e['href'])

	for e in doc.find_all(attr={'class': 'postcontent'}):
		for img in e.find_all('img'):
			
