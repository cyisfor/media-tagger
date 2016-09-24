import syspath
from comic import findComicByTitle, findMedium
from favorites.parse import parse
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

dpat = re.compile("Next: >>([0-9]+)")

def find_next(source):
	temp = io.BytesIO()
	myretrieve(source+'.json',temp)
	doc = json.loads(temp.getvalue().decode('utf-8'))
	description = doc['description']
	m = dpat.match(description)
	assert m
	return "https://derpibooru.org/"+m.group(1)

while True:
	which += 1
	print("Looking for page",hex(which))
	source = find_next(source)
	print(source)
	medium = parse(source)
	print("got it!",medium)
	findMedium(comic,which,medium)
