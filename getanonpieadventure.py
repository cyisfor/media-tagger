import syspath
from comic import findComicByTitle, findMedium
from favorites.parse import parse,parsers as _
import db

from setupurllib import myretrieve

import re,tempfile,json,io

comic = findComicByTitle("Anon's Pie Adventure")

which,medium = db.execute("SELECT which,medium FROM comicPage WHERE comic = $1 ORDER BY medium DESC LIMIT 1",
													(comic,))[0]

# sigh
# why can't the explicit ones also link to the next ones?
# why can't there be an explicit version of the comic?
overrides = {
	1107315: 1107280,
}

print("current",which,hex(medium))
source = db.execute("SELECT uri FROM urisources WHERE id IN (select unnest(sources) FROM media WHERE id = $1) AND uri SIMILAR TO $2",
										(medium,'https://derpibooru.org/[0-9]+'))
assert(len(source) == 1)
source = source[0][0]

# sighhhh
class Source:
	def __init__(self,source):
		self.source = overrides.get(source,source)
	def uri(self):
		return "https://derpibooru.org/"+str(self.source)
	def json(self):
		return "https://derpibooru.org/"+str(self.source)+'.json'
	def advance(self,source):
		self.source = overrides.get(source,source)
	def __repr__(self):
		return repr(self.source)
	
print('initial source',source)
m = re.compile('[0-9]+').search(source)
m = int(m.group(0))
source = Source(m)

dpat = re.compile("Next: >>([0-9]+)")

def find_next(source):
	temp = io.BytesIO()
	myretrieve(source.json(),temp)
	doc = json.loads(temp.getvalue().decode('utf-8'))
	description = doc['description']
	m = dpat.match(description)
	assert m
	source.advance(int(m.group(1)))

while True:
	which += 1
	print("Looking for page",hex(which))
	find_next(source)
	print('found source',source)
	medium = parse(source.uri())
	print("got it!",medium)
	findMedium(comic,which,medium)
